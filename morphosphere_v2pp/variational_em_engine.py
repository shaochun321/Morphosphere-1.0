"""Variational EM Engine — Formal E-step / M-step optimization for J[ρ].

Replaces the hardcoded weight vector in compute_variational_objective()
with iterative parameter estimation:

  E-step: Given θ, compute ρ_k posterior for all windows
  M-step: Given ρ, update θ (lambda weights) to maximize J[ρ; θ]

Converges when |J^(t) - J^(t-1)| < ε.

This module is external analysis — it does NOT modify mainline facts.
"""
from __future__ import annotations
import math, json, uuid, copy
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

def _now(): return datetime.now(timezone.utc).isoformat()
def _jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"
def _jdump(x): return json.dumps(x, separators=(",",":"), ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 1. EM Parameters
# ═══════════════════════════════════════════════════════════════

@dataclass
class EMParams:
    """Learnable parameters for the variational objective."""
    # Lambda weights for 4-source fusion
    lambda_L: float = 0.30    # RLIS
    lambda_C: float = 0.25    # Counter-Masking
    lambda_H: float = 0.25    # HG-FHPMS
    lambda_B: float = 0.20    # BottomMotion

    # J[ρ] component weights (7 terms + 3 bonuses)
    w_motion: float = 1.0
    w_prx: float = 0.8
    w_xin_cons: float = 1.2
    w_r_core: float = 1.5
    w_p_band: float = 0.8
    w_unresolved: float = -1.0   # penalty
    w_drift: float = -0.5        # penalty
    w_writeback: float = -0.3    # penalty

    def to_dict(self):
        return {k: round(v, 6) for k, v in self.__dict__.items()}

    def copy(self):
        return EMParams(**self.__dict__)


# ═══════════════════════════════════════════════════════════════
# 2. Softmax utility
# ═══════════════════════════════════════════════════════════════

def _softmax(scores: dict) -> dict:
    max_s = max(scores.values())
    exps = {k: math.exp(v - max_s) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


# ═══════════════════════════════════════════════════════════════
# 3. E-Step: Compute ρ posterior given θ
# ═══════════════════════════════════════════════════════════════

def e_step(conn, run_id, adapters, windows, params: EMParams):
    """E-step: compute ρ_k for all (adapter, window) using current θ.

    Returns rho_all: Dict[(adapter_name, k), Dict[component, float]]
    """
    import pipeline_engine as eng

    rho_all = {}
    meta_all = {"fhpms": [], "rlis": [], "cm": [], "bm": []}

    for adapter in adapters:
        aname = adapter.adapter_name
        for k in range(1, windows):
            # Query four-source scores using current lambda
            rlis_scores, rlis_meta = eng._compute_rlis_scores(conn, run_id, aname, k)
            cm_scores, cm_meta = eng._compute_counter_mask_scores(conn, run_id, aname, k)
            fhpms_scores, fhpms_meta = eng._compute_fhpms_scores(conn, run_id, aname, k)
            bm_scores, bm_meta = eng._compute_bottom_motion_scores(conn, run_id, aname, k, windows)

            components = ["p_core", "p_band", "r_core", "r_band", "m_band", "x_true", "u"]
            fused = {}
            for z in components:
                fused[z] = (params.lambda_L * rlis_scores[z] +
                           params.lambda_C * cm_scores[z] +
                           params.lambda_H * fhpms_scores[z] +
                           params.lambda_B * bm_scores[z])

            rho = _softmax(fused)
            rho_all[(aname, k)] = rho

            meta_all["fhpms"].append(fhpms_meta)
            meta_all["rlis"].append(rlis_meta)
            meta_all["cm"].append(cm_meta)
            meta_all["bm"].append(bm_meta)

    return rho_all, meta_all


# ═══════════════════════════════════════════════════════════════
# 4. Compute J[ρ; θ] — Variational Objective
# ═══════════════════════════════════════════════════════════════

def compute_J(rho_all, xin_stats, drift, params: EMParams, meta_all=None):
    """Compute J[ρ; θ] using current parameters."""
    n = max(len(rho_all), 1)

    # J_motion: bottom-motion fit
    if meta_all and meta_all.get("bm"):
        avg_fit = sum(m.get("fit_score", 0.5) for m in meta_all["bm"]) / max(len(meta_all["bm"]), 1)
    else:
        avg_fit = 0.5
    j_motion = avg_fit

    # J_prx: distribution stability (lower entropy = more peaked = better)
    avg_entropy = 0.0
    for rho in rho_all.values():
        h = -sum(v * math.log(max(v, 1e-10)) for v in rho.values())
        avg_entropy += h
    avg_entropy /= n
    max_entropy = -7 * (1/7) * math.log(1/7)
    j_prx = 1.0 - (avg_entropy / max_entropy)

    # J_xin_conservation
    gap = xin_stats.get("conservation_gap", 1.0)
    j_xin_cons = max(0, 1.0 - gap)

    # J_r_core
    r_core_count = sum(1 for rho in rho_all.values() if rho.get("r_core", 0) > 0.15)
    j_r_core = r_core_count / n

    # J_p_band
    p_band_count = sum(1 for rho in rho_all.values() if rho.get("p_band", 0) > 0.10)
    j_p_band = p_band_count / n

    # J_unresolved (penalty)
    u_avg = sum(rho.get("u", 0) for rho in rho_all.values()) / n
    j_unresolved = u_avg

    # J_drift (penalty)
    j_drift = drift

    # Potential subsidy bonus
    phi_bonus = 0.0
    if meta_all and meta_all.get("fhpms"):
        phi_avg = sum(m.get("potential_subsidy", 0) for m in meta_all["fhpms"]) / max(len(meta_all["fhpms"]), 1)
        phi_bonus = phi_avg * 0.1

    # Total J
    j_total = (params.w_motion * j_motion +
               params.w_prx * j_prx +
               params.w_xin_cons * j_xin_cons +
               params.w_r_core * j_r_core +
               params.w_p_band * j_p_band +
               params.w_unresolved * j_unresolved +
               params.w_drift * j_drift +
               phi_bonus)

    return {
        "j_motion": j_motion, "j_prx": j_prx, "j_xin_cons": j_xin_cons,
        "j_r_core": j_r_core, "j_p_band": j_p_band,
        "j_unresolved": j_unresolved, "j_drift": j_drift,
        "phi_bonus": phi_bonus, "j_total": j_total,
    }


# ═══════════════════════════════════════════════════════════════
# 5. M-Step: Update θ via gradient ascent on J[ρ; θ]
# ═══════════════════════════════════════════════════════════════

def m_step(conn, run_id, adapters, windows, params: EMParams,
           rho_all, meta_all, xin_stats, drift, lr=0.01):
    """M-step: numerical gradient ascent on J w.r.t. θ.

    Returns updated EMParams.
    """
    new_params = params.copy()

    # Compute gradient for lambda weights via finite differences
    eps = 0.005
    base_J = compute_J(rho_all, xin_stats, drift, params, meta_all)["j_total"]

    # Gradient for lambda_L
    for attr in ["lambda_L", "lambda_C", "lambda_H", "lambda_B"]:
        p_plus = params.copy()
        setattr(p_plus, attr, getattr(p_plus, attr) + eps)
        # Re-normalize lambdas to sum to 1
        lam_sum = p_plus.lambda_L + p_plus.lambda_C + p_plus.lambda_H + p_plus.lambda_B
        p_plus.lambda_L /= lam_sum
        p_plus.lambda_C /= lam_sum
        p_plus.lambda_H /= lam_sum
        p_plus.lambda_B /= lam_sum

        # Re-run E-step with perturbed params
        rho_plus, meta_plus = e_step(conn, run_id, adapters, windows, p_plus)
        J_plus = compute_J(rho_plus, xin_stats, drift, p_plus, meta_plus)["j_total"]

        grad = (J_plus - base_J) / eps
        current_val = getattr(new_params, attr)
        setattr(new_params, attr, current_val + lr * grad)

    # Gradient for J component weights
    for attr in ["w_motion", "w_prx", "w_xin_cons", "w_r_core", "w_p_band"]:
        p_plus = params.copy()
        setattr(p_plus, attr, getattr(p_plus, attr) + eps)
        J_plus = compute_J(rho_all, xin_stats, drift, p_plus, meta_all)["j_total"]
        grad = (J_plus - base_J) / eps
        current_val = getattr(new_params, attr)
        setattr(new_params, attr, max(0.1, current_val + lr * grad))

    # Normalize lambdas to sum to 1
    lam_sum = new_params.lambda_L + new_params.lambda_C + new_params.lambda_H + new_params.lambda_B
    new_params.lambda_L = max(0.05, new_params.lambda_L / lam_sum)
    new_params.lambda_C = max(0.05, new_params.lambda_C / lam_sum)
    new_params.lambda_H = max(0.05, new_params.lambda_H / lam_sum)
    new_params.lambda_B = max(0.05, new_params.lambda_B / lam_sum)
    # Re-normalize after floor
    lam_sum = new_params.lambda_L + new_params.lambda_C + new_params.lambda_H + new_params.lambda_B
    new_params.lambda_L /= lam_sum
    new_params.lambda_C /= lam_sum
    new_params.lambda_H /= lam_sum
    new_params.lambda_B /= lam_sum

    return new_params


# ═══════════════════════════════════════════════════════════════
# 6. Full EM Loop
# ═══════════════════════════════════════════════════════════════

class VariationalEMEngine:
    """Full EM optimization for the variational objective J[ρ].

    Each iteration:
      E-step: compute ρ posterior given current θ
      M-step: update θ to maximize J[ρ; θ]
      Check convergence: |ΔJ| < ε
    """

    def __init__(self, conn, run_id, max_iter=20, lr=0.01, eps=0.01):
        self.conn = conn
        self.run_id = run_id
        self.max_iter = max_iter
        self.lr = lr
        self.eps = eps
        self.history = []

    def run(self, adapters, windows, initial_params=None):
        """Run full EM optimization. Returns (converged_params, history)."""
        params = initial_params or EMParams()

        print(f"  EM Optimization: max_iter={self.max_iter}, lr={self.lr}, eps={self.eps}")
        print(f"  Initial λ: L={params.lambda_L:.3f} C={params.lambda_C:.3f} "
              f"H={params.lambda_H:.3f} B={params.lambda_B:.3f}")

        prev_J = None

        for t in range(1, self.max_iter + 1):
            # E-step
            rho_all, meta_all = e_step(self.conn, self.run_id, adapters, windows, params)

            # Compute xin_stats from DB
            _xi_total = self.conn.execute(
                "SELECT COUNT(*) FROM xi_residue_record WHERE run_id=?",
                (self.run_id,)).fetchone()[0]
            _xi_closed = self.conn.execute(
                "SELECT COUNT(*) FROM xi_decay_policy WHERE run_id=? "
                "AND current_state IN ('discard_after_audit','decaying')",
                (self.run_id,)).fetchone()[0]
            _xi_active = _xi_total - _xi_closed
            conservation_gap = abs(_xi_total - (_xi_active + _xi_closed))

            xin_stats = {
                "conservation_gap": conservation_gap,
                "xin_true": sum(1 for r in rho_all.values() if r["x_true"] > 0.2),
            }

            # Compute drift from previous iteration
            if self.history:
                prev_rho = self.history[-1]["rho_all"]
                drift = 0.0
                for key in rho_all:
                    if key in prev_rho:
                        for z in ["p_core", "p_band", "r_core", "r_band", "m_band", "x_true", "u"]:
                            drift += abs(rho_all[key][z] - prev_rho[key][z])
                drift /= max(len(rho_all), 1)
            else:
                drift = 0.0

            # Compute J
            J_result = compute_J(rho_all, xin_stats, drift, params, meta_all)
            J_total = J_result["j_total"]

            # Convergence check
            delta_J = abs(J_total - prev_J) if prev_J is not None else float("inf")
            converged = (t > 1 and delta_J < self.eps)

            # Record
            iteration_record = {
                "iteration": t,
                "J_total": round(J_total, 6),
                "delta_J": round(delta_J, 6),
                "params": params.to_dict(),
                "J_components": {k: round(v, 4) for k, v in J_result.items()},
                "rho_all": rho_all,
                "converged": converged,
            }
            self.history.append(iteration_record)

            # Write to DB
            self.conn.execute(
                "INSERT INTO v37421_em_iteration_log "
                "(record_id,run_id,iteration,j_total,delta_j,"
                "lambda_l,lambda_c,lambda_h,lambda_b,"
                "w_motion,w_prx,w_xin_cons,w_r_core,w_p_band,"
                "converged,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("em"), self.run_id, t, J_total, delta_J,
                 params.lambda_L, params.lambda_C, params.lambda_H, params.lambda_B,
                 params.w_motion, params.w_prx, params.w_xin_cons,
                 params.w_r_core, params.w_p_band,
                 1 if converged else 0, _now()))

            print(f"    Iter {t:2d}: J={J_total:.4f}  ΔJ={delta_J:.4f}  "
                  f"λ=[{params.lambda_L:.3f},{params.lambda_C:.3f},"
                  f"{params.lambda_H:.3f},{params.lambda_B:.3f}]"
                  f"{'  CONVERGED' if converged else ''}")

            if converged:
                break

            prev_J = J_total

            # M-step: update params
            params = m_step(self.conn, self.run_id, adapters, windows,
                           params, rho_all, meta_all, xin_stats, drift, self.lr)

        # Write converged params
        self.conn.execute(
            "INSERT INTO v37421_em_converged_params "
            "(record_id,run_id,total_iterations,final_j,converged,"
            "lambda_l,lambda_c,lambda_h,lambda_b,"
            "w_motion,w_prx,w_xin_cons,w_r_core,w_p_band,"
            "params_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("emc"), self.run_id, len(self.history),
             J_total, 1 if converged else 0,
             params.lambda_L, params.lambda_C, params.lambda_H, params.lambda_B,
             params.w_motion, params.w_prx, params.w_xin_cons,
             params.w_r_core, params.w_p_band,
             _jdump(params.to_dict()), _now()))

        self.conn.commit()
        return params, self.history
