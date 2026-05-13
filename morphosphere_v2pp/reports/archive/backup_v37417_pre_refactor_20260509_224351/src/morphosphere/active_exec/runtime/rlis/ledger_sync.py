"""
Proxy for RLIS (Relativistic Ledger Information Store)
V37.4.12 Blueprint implementation.
"""
from typing import Dict, Any, List, Optional
import sqlite3
import uuid
import datetime
import math
import json

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _jdump(obj: Any) -> str:
    return json.dumps(obj) if obj else "[]"

class RLISLedgerSync:
    """
    Proxy for writing RLIS external ledger events, Gamma sync,
    Minkowski-like audit intervals, and audit light cones.
    Does not write back to mainline.
    """
    # Information speed limit (not physical c, just audit propagation bound)
    C_I = 10.0
    LAMBDA_PHI = 0.5

    def __init__(self, conn: sqlite3.Connection, run_id: str):
        self.conn = conn
        self.run_id = run_id

    def record_event(self, ledger_time: float, envelope_ref: str,
                     x_proj: float = 0.0, y_proj: float = 0.0, z_proj: float = 0.0,
                     async_phase: float = 0.0) -> str:
        """Record a spacetime event in the external ledger."""
        event_id = _uid("rlev")
        self.conn.execute(
            "INSERT INTO rlis_ledger_event_spacetime "
            "(ledger_event_id, ledger_time, x_proj, y_proj, z_proj, async_phase, "
            "external_envelope_ref, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (event_id, ledger_time, x_proj, y_proj, z_proj, async_phase, envelope_ref, _now())
        )
        return event_id

    def compute_gamma_sync(self, event_id: str, process_window_id: str, sync_strength: float) -> str:
        """Compute Gamma sync and record it. Triggers audit warnings but doesn't block mainline."""
        sync_id = _uid("rlsyn")
        verdict = "strict_hit" if sync_strength >= 0.8 else "low_sync_warning"

        self.conn.execute(
            "INSERT INTO rlis_gamma_sync_binding "
            "(sync_id, ledger_event_id, process_window_id, gamma_strength, sync_verdict, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (sync_id, event_id, process_window_id, sync_strength, verdict, _now())
        )
        return sync_id

    def record_delta_f(self, event_id: str, df_p: float, df_r: float, df_x: float,
                       df_m: float = 0.0, df_u: float = 0.0) -> str:
        """Record the Free Energy Variation split (all 5 components per v1.1 §7)."""
        var_id = _uid("rlvar")
        total_df = df_p + df_r + df_x + df_m + df_u

        self.conn.execute(
            "INSERT INTO rlis_free_energy_variation "
            "(variation_id, ledger_event_id, free_energy_total, delta_f, created_at) "
            "VALUES (?,?,?,?,?)",
            (var_id, event_id, 100.0, total_df, _now())
        )

        split_id = _uid("rlsplt")
        self.conn.execute(
            "INSERT INTO rlis_delta_f_split "
            "(split_id, variation_id, delta_f_p, delta_f_r, delta_f_x, delta_f_m, delta_f_u, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (split_id, var_id, df_p, df_r, df_x, df_m, df_u, _now())
        )
        return var_id

    def compute_minkowski_interval(self, event_1_id: str, event_2_id: str) -> Optional[str]:
        """Compute Minkowski-like information audit interval s_L^2.
        v1.1 §7: s_L^2 = c_I^2 * dt^2 - ||dx||^2 - lambda_phi * dphi^2
        c_I is information audit propagation bound, NOT physical light speed.
        """
        e1 = self.conn.execute(
            "SELECT ledger_time, x_proj, y_proj, z_proj, async_phase "
            "FROM rlis_ledger_event_spacetime WHERE ledger_event_id=?", (event_1_id,)
        ).fetchone()
        e2 = self.conn.execute(
            "SELECT ledger_time, x_proj, y_proj, z_proj, async_phase "
            "FROM rlis_ledger_event_spacetime WHERE ledger_event_id=?", (event_2_id,)
        ).fetchone()
        if not e1 or not e2:
            return None

        dt = (e2[0] or 0) - (e1[0] or 0)
        dx = math.sqrt(((e2[1] or 0)-(e1[1] or 0))**2 + ((e2[2] or 0)-(e1[2] or 0))**2 + ((e2[3] or 0)-(e1[3] or 0))**2)
        dphi = abs((e2[4] or 0) - (e1[4] or 0))

        s_L_sq = self.C_I**2 * dt**2 - dx**2 - self.LAMBDA_PHI * dphi**2

        if s_L_sq > 0:
            causal = "timelike"
        elif s_L_sq < -1e-9:
            causal = "spacelike"
        else:
            causal = "lightlike"

        audit_id = _uid("rlmi")
        self.conn.execute(
            "INSERT INTO rlis_minkowski_audit_interval "
            "(audit_interval_id, event_1_id, event_2_id, interval_squared, "
            "information_speed_limit, causal_status, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (audit_id, event_1_id, event_2_id, s_L_sq, self.C_I, causal, _now())
        )
        return audit_id

    def build_light_cone(self, apex_event_id: str, all_event_ids: List[str]) -> Optional[str]:
        """Build an audit light cone around an apex event.
        Classifies all other events as forward-cone, backward-cone, or spacelike-exterior.
        """
        apex = self.conn.execute(
            "SELECT ledger_time, x_proj, y_proj, z_proj, async_phase "
            "FROM rlis_ledger_event_spacetime WHERE ledger_event_id=?", (apex_event_id,)
        ).fetchone()
        if not apex:
            return None

        forward = []
        backward = []
        spacelike = []

        for eid in all_event_ids:
            if eid == apex_event_id:
                continue
            other = self.conn.execute(
                "SELECT ledger_time, x_proj, y_proj, z_proj, async_phase "
                "FROM rlis_ledger_event_spacetime WHERE ledger_event_id=?", (eid,)
            ).fetchone()
            if not other:
                continue

            dt = (other[0] or 0) - (apex[0] or 0)
            dx = math.sqrt(((other[1] or 0)-(apex[1] or 0))**2 + ((other[2] or 0)-(apex[2] or 0))**2 + ((other[3] or 0)-(apex[3] or 0))**2)
            dphi = abs((other[4] or 0) - (apex[4] or 0))
            s_sq = self.C_I**2 * dt**2 - dx**2 - self.LAMBDA_PHI * dphi**2

            if s_sq >= 0:
                if dt > 0:
                    forward.append(eid)
                else:
                    backward.append(eid)
            else:
                spacelike.append(eid)

        cone_id = _uid("rlcone")
        self.conn.execute(
            "INSERT INTO rlis_audit_light_cone "
            "(cone_id, apex_event_id, forward_cone_refs_json, "
            "backward_cone_refs_json, spacelike_exterior_refs_json, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (cone_id, apex_event_id, _jdump(forward), _jdump(backward), _jdump(spacelike), _now())
        )
        return cone_id
