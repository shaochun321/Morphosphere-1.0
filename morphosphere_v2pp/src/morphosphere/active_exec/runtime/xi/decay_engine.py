"""Xi Residue Decay Engine (V8.3 §8 / V8.5 §7).

Manages the lifecycle of unresolved residuals (Xi / Ξ):
  held → decaying → proto_candidate → promoted (→ O_candidate review)
                  → quarantined → discarded_after_audit

Xi is NOT a garbage bin (v8.3 §8.1). It is a structured carrier for:
  Y_m = P_m + R_m + Ξ_m + ε_num_m

Hard rules (v8.5 §7):
  - Xi cannot directly become P/R/Omega/T_seed
  - Xi cannot carry semantic labels
  - Xi cannot bypass O_candidate
  - Xi cannot accumulate infinitely (v8.5 §7.1)

Xi types (v8.3 §8.2):
  stochastic_noise, unresolved_memory, proto_structure,
  boundary_uncertain, numerical_residue, unknown
"""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

# ═══════════════════════════════════════════════════════════════
# Xi States (V8.5 §7.1)
# ═══════════════════════════════════════════════════════════════

XI_STATES = [
    "held",                # Temporarily stored, awaiting evaluation
    "decaying",            # Actively decaying toward discard
    "proto_candidate",     # Shows cross-scale persistence or boundary sensitivity
    "promoted",            # Promoted to O_candidate review (never directly to P/R)
    "quarantined",         # Isolated, not entering T
    "discarded_after_audit",  # Audited and discarded
]

XI_TYPES = [
    "stochastic_noise",
    "unresolved_memory",
    "proto_structure",
    "boundary_uncertain",
    "numerical_residue",
    "unknown",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class XiDecayEngine:
    """Manages Xi residue lifecycle.

    Usage:
        engine = XiDecayEngine(conn, run_id)
        engine.step_window(window_k=5)  # evaluate all Xi for this window
        engine.get_lifecycle_summary()
    """

    # Decay parameters
    DEFAULT_DECAY_RATE = 0.15         # per-window mass reduction
    DISCARD_MASS_THRESHOLD = 0.02     # below this → eligible for discard
    PROTO_PERSISTENCE_THRESHOLD = 3   # windows before proto_candidate
    MAX_HELD_WINDOWS = 10             # max windows in held state
    MAX_TOTAL_XI_MASS = 50.0          # accumulation budget per run

    def __init__(
        self,
        conn: "sqlite3.Connection",
        run_id: str,
        decay_rate: float = DEFAULT_DECAY_RATE,
    ):
        self.conn = conn
        self.run_id = run_id
        self.decay_rate = decay_rate

    def step_window(self, window_k: int) -> Dict[str, Any]:
        """Evaluate all Xi records for the current window.

        V8.5 §7.1 default rules:
          - No growth, no relation/occupancy support → decaying
          - Mass → 0 over consecutive windows → discarded_after_audit
          - Weak persistence but unstructured → held/decaying
          - Cross-scale persistence or boundary sensitivity → proto_candidate
          - Masking + ledger + transport support → promoted (to O_candidate review)
          - Numerical residue → solver diagnostics, not structural carry

        Returns:
            Summary of state transitions.
        """
        rows = self.conn.execute(
            "SELECT xi_id, xi_type, xi_state, mass_current, mass_previous, "
            "decay_rate, persistence_window_count, relation_support_score, "
            "occupancy_support_score, carryover_allowed "
            "FROM xi_residue_record WHERE run_id=? AND xi_state NOT IN "
            "('discarded_after_audit','promoted')",
            (self.run_id,)
        ).fetchall()

        transitions = {"decayed": 0, "discarded": 0, "proto_promoted": 0,
                        "promoted": 0, "quarantined": 0, "held": 0}

        for row in rows:
            xi_id = row[0]
            xi_type = row[1]
            state = row[2]
            mass_curr = row[3] or 1.0
            mass_prev = row[4] or mass_curr
            dr = row[5] or self.decay_rate
            persist = row[6] or 0
            rel_support = row[7] or 0.0
            occ_support = row[8] or 0.0

            new_state = state
            new_mass = mass_curr
            audit_reason = ""

            # --- Rule evaluation ---

            # 1. Numerical residue → quarantine immediately
            if xi_type == "numerical_residue":
                new_state = "quarantined"
                audit_reason = "numerical_residue_to_solver_diagnostics"
                transitions["quarantined"] += 1

            # 2. Cross-scale persistence + boundary sensitivity → proto_candidate
            elif persist >= self.PROTO_PERSISTENCE_THRESHOLD and (
                rel_support > 0.2 or occ_support > 0.2
            ):
                if state != "proto_candidate":
                    new_state = "proto_candidate"
                    audit_reason = "cross_scale_persistence_with_support"
                    transitions["proto_promoted"] += 1
                else:
                    # Already proto — check promotion readiness
                    if rel_support > 0.5 and occ_support > 0.3:
                        new_state = "promoted"
                        audit_reason = "masking_ledger_transport_joint_support"
                        transitions["promoted"] += 1
                    else:
                        transitions["held"] += 1

            # 3. No growth, no support → decaying
            elif mass_curr <= mass_prev and rel_support < 0.1 and occ_support < 0.1:
                new_mass = mass_curr * (1.0 - dr)

                if new_mass < self.DISCARD_MASS_THRESHOLD:
                    new_state = "discarded_after_audit"
                    audit_reason = f"mass_below_threshold_{new_mass:.4f}"
                    transitions["discarded"] += 1
                elif state != "decaying":
                    new_state = "decaying"
                    audit_reason = "no_growth_no_support"
                    transitions["decayed"] += 1
                else:
                    transitions["decayed"] += 1

            # 4. Held too long → force decay
            elif state == "held" and persist >= self.MAX_HELD_WINDOWS:
                new_state = "decaying"
                new_mass = mass_curr * (1.0 - dr)
                audit_reason = f"held_exceeded_max_windows_{self.MAX_HELD_WINDOWS}"
                transitions["decayed"] += 1

            # 5. Default: stay held, increment persistence
            else:
                transitions["held"] += 1

            # --- Update record ---
            self.conn.execute(
                "UPDATE xi_residue_record SET "
                "xi_state=?, mass_previous=?, mass_current=?, "
                "persistence_window_count=?, audit_reason=?, updated_at=? "
                "WHERE xi_id=?",
                (new_state, mass_curr, new_mass,
                 persist + 1, audit_reason, _now(), xi_id))

        # --- Accumulation budget check (v8.5 §7.1) ---
        total = self.conn.execute(
            "SELECT SUM(mass_current) FROM xi_residue_record "
            "WHERE run_id=? AND xi_state NOT IN ('discarded_after_audit','promoted')",
            (self.run_id,)
        ).fetchone()
        total_mass = total[0] if total and total[0] else 0.0

        if total_mass > self.MAX_TOTAL_XI_MASS:
            transitions["accumulation_overflow"] = True
            self._force_decay_oldest(total_mass - self.MAX_TOTAL_XI_MASS)

        transitions["total_active_mass"] = round(total_mass, 4)
        transitions["window_k"] = window_k
        return transitions

    def _force_decay_oldest(self, excess_mass: float):
        """Force-decay oldest held Xi when accumulation budget exceeded."""
        rows = self.conn.execute(
            "SELECT xi_id, mass_current FROM xi_residue_record "
            "WHERE run_id=? AND xi_state='held' "
            "ORDER BY persistence_window_count DESC",
            (self.run_id,)
        ).fetchall()

        decayed = 0.0
        for xi_id, mass in rows:
            if decayed >= excess_mass:
                break
            self.conn.execute(
                "UPDATE xi_residue_record SET xi_state='decaying', "
                "mass_current=?, audit_reason='accumulation_budget_force_decay' "
                "WHERE xi_id=?",
                (mass * 0.5, xi_id))
            decayed += mass * 0.5

    def create_xi_from_residual(
        self,
        hypothesis_id: str,
        xi_type: str = "unknown",
        initial_mass: float = 1.0,
        relation_support: float = 0.0,
        occupancy_support: float = 0.0,
    ) -> str:
        """Create a new Xi record from P/R decomposition residual.

        V8.3 §8.1: Y_m = P_m + R_m + Ξ_m + ε_num_m
        """
        xi_id = _uid("xi")
        self.conn.execute(
            "INSERT INTO xi_residue_record "
            "(xi_id,run_id,source_hypothesis_id,xi_type,xi_state,"
            "mass_current,mass_previous,decay_rate,"
            "persistence_window_count,relation_support_score,"
            "occupancy_support_score,carryover_allowed,"
            "audit_reason,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (xi_id, self.run_id, hypothesis_id, xi_type, "held",
             initial_mass, initial_mass, self.decay_rate,
             0, relation_support, occupancy_support, 1,
             "created_from_pr_residual", _now()))
        return xi_id

    def apply_carry(self, window_k: int) -> Dict[str, Any]:
        """V8.3 §8.4: Apply Xi carry constraint across windows.

        Ξ_carry(k+1) = decay_rate × Ξ(k) × carry_weight
        """
        rows = self.conn.execute(
            "SELECT xi_id, mass_current, decay_rate, carryover_allowed "
            "FROM xi_residue_record "
            "WHERE run_id=? AND xi_state IN ('held','decaying','proto_candidate') "
            "AND carryover_allowed=1",
            (self.run_id,)
        ).fetchall()

        carried = 0
        for xi_id, mass, dr, _ in rows:
            carry_mass = mass * (1.0 - (dr or self.decay_rate))
            self.conn.execute(
                "UPDATE xi_residue_record SET mass_previous=mass_current, "
                "mass_current=? WHERE xi_id=?",
                (carry_mass, xi_id))
            carried += 1

        return {"carried": carried, "window_k": window_k}

    def get_lifecycle_summary(self) -> Dict[str, Any]:
        """Summary of Xi states for the current run."""
        rows = self.conn.execute(
            "SELECT xi_state, COUNT(*), SUM(mass_current), AVG(persistence_window_count) "
            "FROM xi_residue_record WHERE run_id=? GROUP BY xi_state",
            (self.run_id,)
        ).fetchall()

        summary = {}
        for state, cnt, total_mass, avg_persist in rows:
            summary[state] = {
                "count": cnt,
                "total_mass": round(total_mass or 0, 4),
                "avg_persistence": round(avg_persist or 0, 1),
            }
        return summary
