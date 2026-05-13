"""Ledger Temporal Binding & Free-Energy Routing Engine (V36.8 fix).

Fixes the "free-energy destination routing collapse" identified in the
v36.8 test analysis: currently 79/80 ΔF_ext route to P because the ledger
lacks independent time coordinates and async phase depth.

This module adds:
  1. Ledger temporal coordinates (t_start_L, t_end_L, S_L, φ_L, E_L)
  2. Ledger-window sync kernel Γ(L_m, W_k) with IoU-based matching
  3. Softmax free-energy routing to P/R/X/M/U channels

The routing decomposition is:
  ΔF_{i,k}(m) = Γ(L_m, W_k) × π_i(k,m) × ΔF_ext(m)
where i ∈ {P, R, X, M, U}

Hard rules:
  - Ledger cannot write P/R/Xi directly (v8.5 §1.5)
  - Ledger is read-only for main solver (v36.1 §7)
  - Routing is evidence-based, not default-to-P
"""
from __future__ import annotations
import math, json, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ═══════════════════════════════════════════════════════════════
# Sync Kernel (V36.8 §6)
# ═══════════════════════════════════════════════════════════════

def compute_sync_kernel(
    t_start_L: float, t_end_L: float, s_L: float, phi_L: float, e_L: str,
    t_start_W: float, t_end_W: float, s_W: float, phi_W: float, e_W: str,
    lambda_T: float = 2.0,
    lambda_S: float = 1.0,
    lambda_phi: float = 1.5,
    lambda_E: float = 3.0,
    theta_phi: float = 1.0,
) -> float:
    """Compute sync kernel Γ(L_m, W_k).

    Γ = exp(-λ_T d_T - λ_S d_S - λ_φ d_φ - λ_E d_E)
    """
    # Time IoU
    t_inter = max(0, min(t_end_L, t_end_W) - max(t_start_L, t_start_W))
    t_union = max(1e-9, max(t_end_L, t_end_W) - min(t_start_L, t_start_W))
    d_T = 1.0 - t_inter / t_union

    # Support domain IoU
    s_inter = max(0, min(s_L, s_W))
    s_union = max(1e-9, max(s_L, s_W))
    d_S = 1.0 - s_inter / s_union

    # Async phase distance
    d_phi = abs(phi_L - phi_W) / max(theta_phi, 1e-9)

    # Envelope mismatch
    d_E = 0.0 if e_L == e_W else 1.0

    gamma = math.exp(
        -lambda_T * d_T
        - lambda_S * d_S
        - lambda_phi * d_phi
        - lambda_E * d_E
    )
    return gamma


# ═══════════════════════════════════════════════════════════════
# Softmax Free-Energy Router (V36.8 §7)
# ═══════════════════════════════════════════════════════════════

class FreeEnergyRouter:
    """Routes ΔF_ext to P/R/X/M/U channels based on evidence."""

    def __init__(
        self,
        conn: "sqlite3.Connection",
        run_id: str,
        a_P: float = 1.0, b_P: float = 0.5,
        a_R: float = 0.8, b_R: float = 0.3,
        a_X: float = 0.6, b_X: float = 0.4, c_X: float = 0.3, d_X: float = 0.2, e_X: float = 0.5,
        a_M: float = 0.5,
        a_U: float = 0.4,
    ):
        self.conn = conn
        self.run_id = run_id
        self.params = {
            "a_P": a_P, "b_P": b_P,
            "a_R": a_R, "b_R": b_R,
            "a_X": a_X, "b_X": b_X, "c_X": c_X, "d_X": d_X, "e_X": e_X,
            "a_M": a_M, "a_U": a_U,
        }

    def compute_scores(self, p_mass, p_stability, r_counter, r_boundary,
                       xi_carry_cost, xi_mass, anomaly_mass, async_phase_depth,
                       p_compression_gain, masking_pressure, anomaly_unresolved):
        p = self.params
        s_P = p["a_P"] * p_mass + p["b_P"] * p_stability
        s_R = p["a_R"] * r_counter + p["b_R"] * r_boundary
        s_X = (p["a_X"] * xi_carry_cost + p["b_X"] * xi_mass
               + p["c_X"] * anomaly_mass + p["d_X"] * async_phase_depth
               - p["e_X"] * p_compression_gain)
        s_M = p["a_M"] * masking_pressure
        s_U = p["a_U"] * anomaly_unresolved
        return {"P": s_P, "R": s_R, "X": s_X, "M": s_M, "U": s_U}

    def softmax_route(self, scores):
        max_s = max(scores.values())
        exps = {k: math.exp(v - max_s) for k, v in scores.items()}
        total = sum(exps.values())
        return {k: v / total for k, v in exps.items()}

    def route_delta_f(self, delta_f_ext, window_id,
                      p_mass=0.5, p_stability=0.5,
                      r_counter=0.3, r_boundary=0.2,
                      xi_carry_cost=0.2, xi_mass=0.3,
                      anomaly_mass=0.1, async_phase_depth=0.0,
                      p_compression_gain=0.3,
                      masking_pressure=0.2, anomaly_unresolved=0.1,
                      gamma=1.0):
        scores = self.compute_scores(
            p_mass, p_stability, r_counter, r_boundary,
            xi_carry_cost, xi_mass, anomaly_mass, async_phase_depth,
            p_compression_gain, masking_pressure, anomaly_unresolved)
        probs = self.softmax_route(scores)
        allocations = {k: gamma * probs[k] * delta_f_ext for k in probs}

        routing_id = _uid("frt")
        self.conn.execute(
            "INSERT INTO v368_free_energy_routing "
            "(routing_id,run_id,window_id,delta_f_ext,gamma_sync,"
            "pi_P,pi_R,pi_X,pi_M,pi_U,"
            "alloc_P,alloc_R,alloc_X,alloc_M,alloc_U,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (routing_id, self.run_id, window_id, delta_f_ext, gamma,
             probs["P"], probs["R"], probs["X"], probs["M"], probs["U"],
             allocations["P"], allocations["R"], allocations["X"],
             allocations["M"], allocations["U"], _now()))

        return {
            "routing_id": routing_id,
            "scores": scores,
            "probabilities": probs,
            "allocations": allocations,
            "p_ratio": probs["P"],
        }


class LedgerTemporalBinder:
    """Binds ledger events to ProcessWindows via sync kernel."""

    GAMMA_THRESHOLD = 0.3

    def __init__(self, conn: "sqlite3.Connection", run_id: str):
        self.conn = conn
        self.run_id = run_id

    def bind_ledger_to_windows(self, ledger_events, windows):
        bindings = []
        for le in ledger_events:
            best_gamma = 0.0
            best_window = None
            for w in windows:
                g = compute_sync_kernel(
                    t_start_L=le.get("t_start", 0), t_end_L=le.get("t_end", 1),
                    s_L=le.get("support_domain", 1.0), phi_L=le.get("async_phase", 0.0),
                    e_L=le.get("envelope_ref", ""),
                    t_start_W=w.get("t_start", 0), t_end_W=w.get("t_end", 1),
                    s_W=w.get("support_domain", 1.0), phi_W=w.get("async_phase", 0.0),
                    e_W=w.get("envelope_ref", ""),
                )
                if g > best_gamma:
                    best_gamma = g
                    best_window = w

            bind_result = {
                "ledger_event_id": le.get("event_id", ""),
                "gamma": best_gamma,
                "sync_status": "synced" if best_gamma >= self.GAMMA_THRESHOLD else "unresolved",
            }
            if best_window and best_gamma >= self.GAMMA_THRESHOLD:
                bind_result["window_id"] = best_window.get("window_id", "")
            else:
                bind_result["window_id"] = None
                bind_result["sync_status"] = "ledger_sync_unresolved"

            bindings.append(bind_result)

        return bindings
