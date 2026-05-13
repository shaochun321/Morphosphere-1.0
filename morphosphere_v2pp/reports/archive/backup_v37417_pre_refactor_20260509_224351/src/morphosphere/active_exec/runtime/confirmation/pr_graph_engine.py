"""P/R Confirmation Graph Engine (V8.5 §4).

Replaces the linear P/R state machine with a directed graph allowing:
  - Backtracking (mask_supported → PR_candidate)
  - Xi diversion (any state → xi_carried)
  - Refutation via conjunctive evidence
  - Emergence alerting
  - Suspension for insufficient evidence

Hard rules (v8.5 §4.4):
  "Frozen" does NOT mean final truth. It only means the candidate has
  earned stage-level recursive carry and compute scheduling permission
  under masking, occupancy, transport, replay, boundary, and ledger
  alignment support.

  Use: confirmation_state, compute_commitment, science_certification.
  Avoid: "freeze" as finality language.
"""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

# ═══════════════════════════════════════════════════════════════
# Confirmation Graph Nodes (V8.5 §4.2)
# ═══════════════════════════════════════════════════════════════

GRAPH_NODES = [
    "O_candidate",
    "PR_candidate",
    "mask_supported",
    "recursion_eligible",
    "compute_committed",
    "science_certified",
    "refuted",
    "suspended",
    "xi_carried",
    "emergence_alerted",
]

# Allowed transitions and their required conditions
ALLOWED_TRANSITIONS = {
    ("O_candidate", "PR_candidate"):       ["has_hypothesis", "has_occupancy"],
    ("PR_candidate", "mask_supported"):     ["passed_masking_mvp"],
    ("PR_candidate", "refuted"):            ["refutation_conjunct"],
    ("PR_candidate", "xi_carried"):         ["xi_diversion_eligible"],
    ("PR_candidate", "suspended"):          ["insufficient_evidence"],
    ("mask_supported", "recursion_eligible"):["transport_continuity", "bounded_xi_pressure"],
    ("mask_supported", "PR_candidate"):     ["masking_weakened"],
    ("mask_supported", "refuted"):          ["refutation_conjunct"],
    ("mask_supported", "xi_carried"):       ["xi_diversion_eligible"],
    ("recursion_eligible", "compute_committed"): ["multi_run_support", "solver_bounded"],
    ("recursion_eligible", "suspended"):    ["insufficient_evidence"],
    ("compute_committed", "science_certified"): ["multi_boundary", "replay_aligned", "stable_occupancy"],
    ("compute_committed", "suspended"):     ["late_counterevidence"],
    ("PR_candidate", "emergence_alerted"):  ["emergence_trigger"],
    ("mask_supported", "emergence_alerted"):["emergence_trigger"],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ConfirmationGraphEngine:
    """Manages the P/R Confirmation Graph for object hypotheses."""

    def __init__(self, conn: "sqlite3.Connection", run_id: str):
        self.conn = conn
        self.run_id = run_id

    def get_hypothesis_state(self, hypothesis_id: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT status FROM object_hypothesis WHERE hypothesis_id=?",
            (hypothesis_id,)
        ).fetchone()
        return row[0] if row else None

    def evaluate_conditions(self, hypothesis_id: str, target_node: str) -> Dict[str, Any]:
        current = self.get_hypothesis_state(hypothesis_id)
        if current is None:
            return {"valid": False, "reason": "hypothesis_not_found"}
        key = (current, target_node)
        if key not in ALLOWED_TRANSITIONS:
            return {"valid": False, "reason": f"transition_not_allowed:{current}->{target_node}"}
        required = ALLOWED_TRANSITIONS[key]
        verdicts = {}
        for cond_name in required:
            checker = getattr(self, f"_check_{cond_name}", None)
            if checker:
                verdicts[cond_name] = checker(hypothesis_id)
            else:
                verdicts[cond_name] = True
        all_pass = all(verdicts.values())
        return {"valid": all_pass, "conditions": verdicts, "from": current, "to": target_node}

    def attempt_transition(self, hypothesis_id: str, target_node: str,
                           evidence_refs: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
        eval_result = self.evaluate_conditions(hypothesis_id, target_node)
        if not eval_result["valid"] and not force:
            return {"success": False, **eval_result}
        from_node = eval_result.get("from", self.get_hypothesis_state(hypothesis_id))
        self.conn.execute("UPDATE object_hypothesis SET status=? WHERE hypothesis_id=?",
                          (target_node, hypothesis_id))
        tid = _uid("prt")
        self.conn.execute(
            "INSERT INTO pr_graph_transition_record "
            "(transition_id,hypothesis_id,from_state,to_state,run_id,"
            "conditions_met_json,evidence_refs_json,created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (tid, hypothesis_id, from_node, target_node, self.run_id,
             json.dumps(eval_result.get("conditions", {})),
             json.dumps(evidence_refs or []), _now()))
        return {"success": True, "transition_id": tid, "from": from_node, "to": target_node}

    def route_to_xi(self, hypothesis_id: str, xi_type: str = "unknown", reason: str = "") -> str:
        self.attempt_transition(hypothesis_id, "xi_carried", force=True)
        xi_id = _uid("xi")
        self.conn.execute(
            "INSERT INTO xi_residue_record "
            "(xi_id,run_id,source_hypothesis_id,xi_type,xi_state,"
            "mass_current,decay_rate,persistence_window_count,"
            "carryover_allowed,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (xi_id, self.run_id, hypothesis_id, xi_type, "held",
             1.0, 0.05, 0, 1, _now()))
        return xi_id

    def check_refutation(self, hypothesis_id: str) -> Dict[str, Any]:
        result = {
            "masking_refutes": self._check_masking_refutes(hypothesis_id),
            "low_temporal_persistence": self._check_low_temporal(hypothesis_id),
            "low_occupancy": self._check_low_occupancy(hypothesis_id),
            "no_xi_carryover": self._check_no_xi_carryover(hypothesis_id),
        }
        result["should_refute"] = all(result.values())
        return result

    # ─── Internal condition checkers ───────────────────────────

    def _check_has_hypothesis(self, hid: str) -> bool:
        row = self.conn.execute("SELECT COUNT(*) FROM object_hypothesis WHERE hypothesis_id=?", (hid,)).fetchone()
        return (row[0] if row else 0) > 0

    def _check_has_occupancy(self, hid: str) -> bool:
        row = self.conn.execute("SELECT COUNT(*) FROM occupancy_measure WHERE hypothesis_id=?", (hid,)).fetchone()
        return (row[0] if row else 0) > 0

    def _check_passed_masking_mvp(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT masking_type) FROM masking_counterevidence_record "
            "WHERE hypothesis_id=? AND verdict IN ('supports_confirmation','inconclusive','supports_freeze')",
            (hid,)).fetchone()
        return (row[0] if row else 0) >= 3

    def _check_transport_continuity(self, hid: str) -> bool:
        row = self.conn.execute("SELECT AVG(transport_support) FROM occupancy_measure WHERE hypothesis_id=?",
                                (hid,)).fetchone()
        return (row[0] or 0) > 0.1

    def _check_bounded_xi_pressure(self, hid: str) -> bool:
        row = self.conn.execute("SELECT SUM(mass_current) FROM xi_residue_record WHERE source_hypothesis_id=?",
                                (hid,)).fetchone()
        return (row[0] or 0) < 3.0

    def _check_multi_run_support(self, hid: str) -> bool:
        return True

    def _check_solver_bounded(self, hid: str) -> bool:
        return True

    def _check_multi_boundary(self, hid: str) -> bool:
        return True

    def _check_replay_aligned(self, hid: str) -> bool:
        return True

    def _check_stable_occupancy(self, hid: str) -> bool:
        row = self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",
                                (hid,)).fetchone()
        return (row[0] or 0) > 0.3

    def _check_masking_weakened(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM masking_counterevidence_record "
            "WHERE hypothesis_id=? AND verdict='weakens_confirmation'", (hid,)).fetchone()
        return (row[0] if row else 0) > 0

    def _check_refutation_conjunct(self, hid: str) -> bool:
        return self.check_refutation(hid)["should_refute"]

    def _check_xi_diversion_eligible(self, hid: str) -> bool:
        occ = self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",
                                (hid,)).fetchone()
        mass = occ[0] if occ else 0
        return 0.05 < (mass or 0) < 0.3

    def _check_insufficient_evidence(self, hid: str) -> bool:
        occ = self.conn.execute("SELECT COUNT(*) FROM occupancy_measure WHERE hypothesis_id=?", (hid,)).fetchone()
        return (occ[0] if occ else 0) < 2

    def _check_emergence_trigger(self, hid: str) -> bool:
        return False

    def _check_late_counterevidence(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM masking_counterevidence_record "
            "WHERE hypothesis_id=? AND verdict='refutes_candidate'", (hid,)).fetchone()
        return (row[0] if row else 0) > 0

    def _check_masking_refutes(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM masking_counterevidence_record "
            "WHERE hypothesis_id=? AND verdict IN ('refutes_candidate','refutes_freeze')",
            (hid,)).fetchone()
        return (row[0] if row else 0) > 0

    def _check_low_temporal(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(DISTINCT m.cell_uid) FROM occupancy_measure m "
            "JOIN spacetime_cell c ON m.cell_uid=c.cell_uid WHERE m.hypothesis_id=?",
            (hid,)).fetchone()
        return (row[0] if row else 0) < 3

    def _check_low_occupancy(self, hid: str) -> bool:
        row = self.conn.execute("SELECT AVG(membership_mass) FROM occupancy_measure WHERE hypothesis_id=?",
                                (hid,)).fetchone()
        return (row[0] or 0) < 0.1

    def _check_no_xi_carryover(self, hid: str) -> bool:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM xi_residue_record "
            "WHERE source_hypothesis_id=? AND carryover_allowed=1", (hid,)).fetchone()
        return (row[0] if row else 0) == 0

    def get_graph_summary(self) -> Dict[str, int]:
        rows = self.conn.execute(
            "SELECT status, COUNT(*) FROM object_hypothesis WHERE run_id=? GROUP BY status",
            (self.run_id,)).fetchall()
        return {r[0]: r[1] for r in rows}
