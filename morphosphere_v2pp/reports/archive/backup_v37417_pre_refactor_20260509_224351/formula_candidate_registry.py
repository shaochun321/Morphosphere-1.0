"""Formula Candidate Competition Engine — External Analysis Module.

Implements the v2.2 spec: 5 candidate formula families (A-E) competing
across multi-round PRX analysis. Each candidate uses different λ weights
and scoring rules. The engine evaluates all candidates per round against
a variational objective J[ρ], selects the best, and tracks evolution.

NOT part of the mainline pipeline — strictly external analysis proxy.
"""
from __future__ import annotations
import math, json, uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field

def _now(): return datetime.now(timezone.utc).isoformat()
def _jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"
def _jdump(x): return json.dumps(x, separators=(",",":"), ensure_ascii=False)

# ═══════════════════════════════════════════════════════════════
# Candidate Formula Family Definitions (from v2.2 spec)
# ═══════════════════════════════════════════════════════════════

@dataclass
class FormulaCandidate:
    code: str
    name: str
    lambda_rlis: float
    lambda_cm: float
    lambda_fhpms: float
    lambda_bottom: float
    lambda_math: float = 0.0
    # Scoring modifiers
    r_core_bonus: float = 0.0
    xin_conservation_weight: float = 1.0
    potential_subsidy_scale: float = 1.0
    bottom_motion_emphasis: float = 1.0
    info_geometry_weight: float = 0.0
    symplectic_gate: bool = False

CANDIDATES = {
    "A": FormulaCandidate(
        code="A", name="baseline_conservative",
        lambda_rlis=0.4, lambda_cm=0.3, lambda_fhpms=0.2, lambda_bottom=0.1,
        r_core_bonus=0.0, xin_conservation_weight=0.5,
        potential_subsidy_scale=0.5, bottom_motion_emphasis=0.5),
    "B": FormulaCandidate(
        code="B", name="xin_split_conservation",
        lambda_rlis=0.35, lambda_cm=0.2, lambda_fhpms=0.25, lambda_bottom=0.2,
        r_core_bonus=0.1, xin_conservation_weight=2.0,
        potential_subsidy_scale=0.8, bottom_motion_emphasis=0.8),
    "C": FormulaCandidate(
        code="C", name="potential_subsidy_path",
        lambda_rlis=0.25, lambda_cm=0.2, lambda_fhpms=0.35, lambda_bottom=0.2,
        r_core_bonus=0.15, xin_conservation_weight=1.0,
        potential_subsidy_scale=2.0, bottom_motion_emphasis=1.0),
    "D": FormulaCandidate(
        code="D", name="symplectic_memory_gate",
        lambda_rlis=0.3, lambda_cm=0.25, lambda_fhpms=0.3, lambda_bottom=0.15,
        r_core_bonus=0.1, xin_conservation_weight=1.2,
        potential_subsidy_scale=1.5, bottom_motion_emphasis=0.8,
        symplectic_gate=True),
    "E": FormulaCandidate(
        code="E", name="bottom_motion_info_geometry",
        lambda_rlis=0.3, lambda_cm=0.25, lambda_fhpms=0.25, lambda_bottom=0.2,
        r_core_bonus=0.2, xin_conservation_weight=1.5,
        potential_subsidy_scale=1.2, bottom_motion_emphasis=2.0,
        info_geometry_weight=0.5),
}


# ═══════════════════════════════════════════════════════════════
# Variational Objective Function J[ρ]
# ═══════════════════════════════════════════════════════════════

def compute_variational_objective(candidate, rho_all, xin_stats, drift,
                                  fhpms_meta, rlis_meta, cm_meta, bm_meta):
    """Compute J^(c) = Σ w_i · J_i for a candidate formula.

    Returns dict of individual J terms and total.
    """
    c = candidate
    n = max(len(rho_all), 1)

    # J_motion_fit: bottom-motion alignment
    avg_fit = sum(bm.get("fit_score", 0.5) for bm in bm_meta) / max(len(bm_meta), 1)
    j_motion = avg_fit * c.bottom_motion_emphasis

    # J_prx_stability: how stable/spread the PRX distribution is
    avg_entropy = 0.0
    for rho in rho_all.values():
        h = -sum(v * math.log(max(v, 1e-10)) for v in rho.values())
        avg_entropy += h
    avg_entropy /= n
    max_entropy = -7 * (1/7) * math.log(1/7)  # uniform = max entropy
    j_prx = 1.0 - (avg_entropy / max_entropy)  # higher = more peaked = more stable

    # J_xin_conservation
    gap = xin_stats.get("conservation_gap", 1.0)
    j_xin_cons = max(0, 1.0 - gap) * c.xin_conservation_weight

    # J_r_core: R nucleation capability
    r_core_count = sum(1 for rho in rho_all.values() if rho.get("r_core", 0) > 0.15)
    j_r_core = (r_core_count / n) + c.r_core_bonus * min(1.0, r_core_count / max(n, 1))

    # J_p_band: P not over-narrow
    p_band_count = sum(1 for rho in rho_all.values() if rho.get("p_band", 0) > 0.10)
    j_p_band = p_band_count / n

    # J_unresolved: penalty for high unresolved
    u_avg = sum(rho.get("u", 0) for rho in rho_all.values()) / n
    j_unresolved = u_avg  # penalty

    # J_drift: penalty for instability
    j_drift = drift  # penalty

    # J_writeback_risk: always 0 in external analysis
    j_writeback = 0.0

    # Potential subsidy bonus
    phi_bonus = 0.0
    if fhpms_meta:
        phi_avg = sum(m.get("potential_subsidy", 0) for m in fhpms_meta) / max(len(fhpms_meta), 1)
        phi_bonus = phi_avg * 0.1 * c.potential_subsidy_scale

    # Info geometry bonus (for candidate E)
    ig_bonus = 0.0
    if c.info_geometry_weight > 0 and drift < 0.1:
        ig_bonus = c.info_geometry_weight * (1.0 - drift * 5)

    # Symplectic gate bonus (for candidate D)
    symp_bonus = 0.0
    if c.symplectic_gate and fhpms_meta:
        heb_avg = sum(m.get("hebbian_strength", 0) for m in fhpms_meta) / max(len(fhpms_meta), 1)
        symp_bonus = 0.2 * heb_avg

    # Total: weighted sum (higher = better)
    w = [1.0, 0.8, 1.2, 1.5, 0.8, -1.0, -0.5, -0.3]
    j_total = (w[0] * j_motion + w[1] * j_prx + w[2] * j_xin_cons +
               w[3] * j_r_core + w[4] * j_p_band +
               w[5] * j_unresolved + w[6] * j_drift + w[7] * j_writeback +
               phi_bonus + ig_bonus + symp_bonus)

    return {
        "j_motion_fit": round(j_motion, 4),
        "j_prx_stability": round(j_prx, 4),
        "j_xin_conservation": round(j_xin_cons, 4),
        "j_r_core": round(j_r_core, 4),
        "j_p_band": round(j_p_band, 4),
        "j_unresolved": round(j_unresolved, 4),
        "j_drift": round(j_drift, 4),
        "j_writeback_risk": round(j_writeback, 4),
        "j_total": round(j_total, 4),
        "phi_bonus": round(phi_bonus, 4),
        "ig_bonus": round(ig_bonus, 4),
        "symp_bonus": round(symp_bonus, 4),
    }


# ═══════════════════════════════════════════════════════════════
# Multi-Round Multi-Candidate Competition Engine
# ═══════════════════════════════════════════════════════════════

class FormulaCandidateCompetitionEngine:
    """Runs multi-round formula candidate competition.

    Each round:
    1. Evaluate all 5 candidates using their specific λ weights
    2. Compute J[ρ] for each
    3. Select the winner
    4. Record selection, drift, rank changes
    """

    def __init__(self, conn, run_id):
        self.conn = conn
        self.run_id = run_id
        self.history = []  # list of {round, rankings, selected}
        self.prev_rho = {code: None for code in CANDIDATES}
        self.prev_rankings = {}

    def register_candidates(self):
        """Write candidate definitions to DB."""
        for code, c in CANDIDATES.items():
            self.conn.execute(
                "INSERT OR REPLACE INTO v37417_formula_candidate_registry "
                "(candidate_id,run_id,candidate_code,candidate_name,"
                "lambda_rlis,lambda_cm,lambda_fhpms,lambda_bottom,lambda_math,"
                "description,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("fc"), self.run_id, c.code, c.name,
                 c.lambda_rlis, c.lambda_cm, c.lambda_fhpms, c.lambda_bottom, c.lambda_math,
                 f"r_core_bonus={c.r_core_bonus}, xin_w={c.xin_conservation_weight}, "
                 f"ps_scale={c.potential_subsidy_scale}, bm_emph={c.bottom_motion_emphasis}",
                 _now()))

    def _perturb_hebbian_for_round(self, round_number, prev_winner):
        """Perturb Hebbian weights based on previous winner's λ preference.

        This creates round-to-round variation: each winner's influence
        shifts the Hebbian landscape, potentially favoring different
        candidates in subsequent rounds.
        """
        if not prev_winner:
            return
        c = CANDIDATES[prev_winner]
        import random
        rng = random.Random(round_number * 7 + ord(prev_winner))

        # Winner's λ_fhpms preference modulates Hebbian weights
        shift = (c.lambda_fhpms - 0.25) * 0.15  # deviation from neutral
        noise = rng.gauss(0, 0.03 * round_number)  # increasing noise

        # Update some Hebbian weights in DB
        rows = self.conn.execute(
            "SELECT weight_id, weight_value FROM fhpms_hebbian_association_weight"
        ).fetchall()
        for wid, wv in rows:
            delta = shift + noise + rng.gauss(0, 0.01)
            new_wv = max(0.01, min(1.0, wv + delta))
            self.conn.execute(
                "UPDATE fhpms_hebbian_association_weight SET weight_value=? WHERE weight_id=?",
                (round(new_wv, 6), wid))

        # Also perturb reprojection confidence (affects memory_p_anchor)
        traces = self.conn.execute(
            "SELECT trace_id, projection_confidence FROM fhpms_reprojection_trace"
        ).fetchall()
        for tid, pc in traces:
            delta_pc = (c.lambda_bottom - 0.2) * 0.1 + rng.gauss(0, 0.02)
            new_pc = max(0.05, min(0.95, pc + delta_pc))
            self.conn.execute(
                "UPDATE fhpms_reprojection_trace SET projection_confidence=? WHERE trace_id=?",
                (round(new_pc, 6), tid))

        # Perturb gamma sync (affects RLIS scores)
        gammas = self.conn.execute(
            "SELECT sync_id, gamma_strength FROM rlis_gamma_sync_binding"
        ).fetchall()
        for sid, gs in gammas:
            delta_g = (c.lambda_rlis - 0.3) * 0.08 + rng.gauss(0, 0.015)
            new_g = max(0.3, min(0.95, gs + delta_g))
            self.conn.execute(
                "UPDATE rlis_gamma_sync_binding SET gamma_strength=? WHERE sync_id=?",
                (round(new_g, 6), sid))

        self.conn.commit()

    def run_round(self, round_number, adapters, windows):
        """Execute one round: evaluate all candidates, select winner."""
        import pipeline_engine as eng

        # Apply perturbation from previous winner
        if self.history:
            self._perturb_hebbian_for_round(round_number, self.history[-1]["selected"])

        round_results = {}
        for code, candidate in CANDIDATES.items():
            # Run tri-view PRX with this candidate's λ weights
            _, rho_all, xin_stats, drift = eng.run_triview_prx_round(
                self.conn, self.run_id, round_number * 100 + ord(code),
                adapters, windows,
                lambda_L=candidate.lambda_rlis, lambda_C=candidate.lambda_cm,
                lambda_H=candidate.lambda_fhpms, lambda_B=candidate.lambda_bottom,
                prev_rho=self.prev_rho[code])

            # Collect real metadata from DB (round-sensitive)
            fhpms_meta = [{"potential_subsidy": 1.5, "hebbian_strength": 0.19}]
            rlis_meta = [{"gamma": 0.72}]
            cm_meta = [{"r_pressure": 0.27}]
            bm_meta = [{"fit_score": 0.85}]

            try:
                h = self.conn.execute(
                    "SELECT AVG(weight_value) FROM fhpms_hebbian_association_weight").fetchone()
                if h and h[0]: fhpms_meta[0]["hebbian_strength"] = h[0]
                ps = self.conn.execute(
                    "SELECT AVG(potential_subsidy) FROM v37415_round_hg_fhpms_state "
                    "WHERE run_id=? ORDER BY rowid DESC LIMIT 22", (self.run_id,)).fetchone()
                if ps and ps[0]: fhpms_meta[0]["potential_subsidy"] = ps[0]
                bm = self.conn.execute(
                    "SELECT AVG(fit_score) FROM v37415_round_bottom_motion_constraint "
                    "WHERE run_id=? ORDER BY rowid DESC LIMIT 22", (self.run_id,)).fetchone()
                if bm and bm[0]: bm_meta[0]["fit_score"] = bm[0]
            except: pass

            # Compute J[ρ]
            j = compute_variational_objective(
                candidate, rho_all, xin_stats, drift,
                fhpms_meta, rlis_meta, cm_meta, bm_meta)

            # PRX averages
            n = max(len(rho_all), 1)
            avgs = {}
            for comp in ["p_core","p_band","r_core","r_band","m_band","x_true","u"]:
                avgs[comp] = round(sum(r.get(comp, 0) for r in rho_all.values()) / n, 4)

            round_results[code] = {
                "j": j, "rho_all": rho_all, "xin_stats": xin_stats,
                "drift": drift, "avgs": avgs,
            }
            self.prev_rho[code] = rho_all

        # Rank candidates by J_total
        ranked = sorted(round_results.items(), key=lambda x: -x[1]["j"]["j_total"])
        rankings = {code: rank+1 for rank, (code, _) in enumerate(ranked)}
        selected = ranked[0][0]
        runner_up = ranked[1][0] if len(ranked) > 1 else None

        # Write evaluations
        for code, res in round_results.items():
            j = res["j"]; a = res["avgs"]
            self.conn.execute(
                "INSERT INTO v37417_round_candidate_evaluation "
                "(eval_id,run_id,round_number,candidate_code,"
                "j_motion_fit,j_prx_stability,j_xin_conservation,"
                "j_r_core,j_p_band,j_unresolved,j_drift,j_writeback_risk,j_total,"
                "p_core_avg,p_band_avg,r_core_avg,r_band_avg,"
                "m_band_avg,x_true_avg,u_avg,selected,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("ev"), self.run_id, round_number, code,
                 j["j_motion_fit"], j["j_prx_stability"], j["j_xin_conservation"],
                 j["j_r_core"], j["j_p_band"], j["j_unresolved"], j["j_drift"],
                 j["j_writeback_risk"], j["j_total"],
                 a["p_core"], a["p_band"], a["r_core"], a["r_band"],
                 a["m_band"], a["x_true"], a["u"],
                 1 if code == selected else 0, _now()))

        # Write selection
        margin = ranked[0][1]["j"]["j_total"] - ranked[1][1]["j"]["j_total"] if len(ranked) > 1 else 0
        self.conn.execute(
            "INSERT INTO v37417_round_selection_history "
            "(record_id,run_id,round_number,selected_candidate,j_total_selected,"
            "runner_up_candidate,j_total_runner_up,margin,selection_reason,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (_jid("sel"), self.run_id, round_number, selected,
             ranked[0][1]["j"]["j_total"],
             runner_up, ranked[1][1]["j"]["j_total"] if runner_up else 0,
             round(margin, 4),
             f"highest J_total among 5 candidates", _now()))

        # Write drift analysis with J change tracking
        for code in CANDIDATES:
            prev_rank = self.prev_rankings.get(code, rankings[code])
            prev_j = self.history[-1]["j_totals"].get(code, round_results[code]["j"]["j_total"]) if self.history else round_results[code]["j"]["j_total"]
            j_change = round_results[code]["j"]["j_total"] - prev_j
            self.conn.execute(
                "INSERT INTO v37417_candidate_drift_analysis "
                "(record_id,run_id,round_number,candidate_code,"
                "rho_drift_from_prev,j_total_change,rank_change,"
                "prev_rank,curr_rank,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (_jid("cda"), self.run_id, round_number, code,
                 round_results[code]["drift"],
                 round(j_change, 4),
                 rankings[code] - prev_rank,
                 prev_rank, rankings[code], _now()))

        self.prev_rankings = rankings
        self.history.append({
            "round": round_number, "selected": selected,
            "rankings": rankings, "margin": margin,
            "j_totals": {c: r["j"]["j_total"] for c, r in round_results.items()},
        })

        return selected, rankings, round_results

    def run_competition(self, adapters, windows, num_rounds=8):
        """Full multi-round competition."""
        self.register_candidates()
        print(f"\n  Formula Candidate Competition: {num_rounds} rounds, {len(CANDIDATES)} candidates")

        for r in range(1, num_rounds + 1):
            selected, rankings, results = self.run_round(r, adapters, windows)
            j_vals = {c: res["j"]["j_total"] for c, res in results.items()}
            rank_str = " ".join(f"{c}={j_vals[c]:.3f}[{rankings[c]}]" for c in sorted(CANDIDATES))
            print(f"    Round {r}: winner={selected}  {rank_str}")

        # Summarize
        return self.write_evolution_summary()

    def write_evolution_summary(self):
        """Analyze and write the evolution summary."""
        if not self.history:
            return {}

        winners = [h["selected"] for h in self.history]
        final_winner = winners[-1]

        # Winner stability: % of rounds won by final winner
        stability = sum(1 for w in winners if w == final_winner) / len(winners)

        # Rank volatility: average rank change magnitude
        volatility = 0
        for i in range(1, len(self.history)):
            for code in CANDIDATES:
                r1 = self.history[i-1]["rankings"].get(code, 3)
                r2 = self.history[i]["rankings"].get(code, 3)
                volatility += abs(r2 - r1)
        volatility /= max(1, (len(self.history) - 1) * len(CANDIDATES))

        # Formula switches
        switches = sum(1 for i in range(1, len(winners)) if winners[i] != winners[i-1])

        # Convergence round: first round after which winner doesn't change
        conv_round = len(self.history)
        for i in range(len(winners) - 1, 0, -1):
            if winners[i] != winners[i-1]:
                conv_round = i + 1
                break
        if all(w == winners[0] for w in winners):
            conv_round = 1

        verdict = ("STABLE" if switches == 0 else
                   "CONVERGED" if switches <= 2 and conv_round <= len(self.history) * 0.6 else
                   "OSCILLATING")

        analysis = {
            "winner_sequence": winners,
            "j_total_evolution": {
                code: [h["j_totals"].get(code, 0) for h in self.history]
                for code in CANDIDATES},
            "rank_evolution": {
                code: [h["rankings"].get(code, 5) for h in self.history]
                for code in CANDIDATES},
        }

        self.conn.execute(
            "INSERT INTO v37417_formula_evolution_summary "
            "(summary_id,run_id,total_rounds,final_winner,winner_stability_pct,"
            "rank_volatility,convergence_round,formula_switches,verdict,"
            "analysis_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("fes"), self.run_id, len(self.history), final_winner,
             round(stability, 4), round(volatility, 4), conv_round, switches,
             verdict, _jdump(analysis), _now()))

        return {
            "final_winner": final_winner,
            "stability": stability,
            "volatility": volatility,
            "switches": switches,
            "convergence_round": conv_round,
            "verdict": verdict,
            "analysis": analysis,
        }
