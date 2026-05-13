"""Variational Xin & Information-Energy Metric Engine (V36/V36.1).

Phase 6: Implements the high-level relationship layer:

1. Dissipative source registry (V36 §3.3)
2. Variational state vector construction (V36.1 §3)
3. Lagrangian term decomposition (V36.1 §4)
4. Euler-Lagrange residual → variational Xin (V36.1 §4.2)
5. Information-energy metric d_IE (V36.1 §5)
6. Relation readout proxy (V36.1 §6)

Mathematical governance (v8.5):
  - All Lagrangian coefficients are meta-proxies, not physical constants
  - mu_IE != real physics metric (V36 §4.4)
  - Relation readout is strictly read-only, no semantic label writeback
  - d_IE computed only within confirmed hyperedge neighborhoods
"""
from __future__ import annotations
import json, math, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3


def _now():
    return datetime.now(timezone.utc).isoformat()

def _uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ═══════════════════════════════════════════════════════════════
# Variational Xin Engine
# ═══════════════════════════════════════════════════════════════

class VariationalXinEngine:
    """Computes variational Xin from Euler-Lagrange residuals.

    V36.1 §4.2:
      Xin_var(m) = ||EL_m|| + omega_B * |B_m| + omega_C * ConstraintViolation_m

    where EL_m is the Euler-Lagrange residual of the action functional S_IE[Gamma].
    """

    # Lagrangian term weights (meta-proxies, not physical constants)
    DEFAULT_WEIGHTS = {
        "L_track": 1.0,        # tracking cost (transport persistence)
        "L_ledger": 0.8,       # external ledger coupling
        "L_xin": 0.6,          # Xin residual cost
        "L_boundary": 0.4,     # boundary interaction
        "L_signal": 0.5,       # signal field coupling
        "L_curvature": 0.3,    # geometric curvature
    }

    # Xin combination weights
    OMEGA_B = 0.3   # boundary term weight
    OMEGA_C = 0.5   # constraint violation weight

    def __init__(
        self,
        conn: "sqlite3.Connection",
        run_id: str,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.conn = conn
        self.run_id = run_id
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def build_state_vector(
        self,
        cell_uid: str,
        window_id: str,
    ) -> Dict[str, float]:
        """Construct variational state vector from SPMS data.

        V36.1 §3: phi = (phi_info, phi_geo, phi_transport, phi_boundary, phi_signal, phi_occupancy)
        """
        # Query information fiber
        fib = self.conn.execute(
            "SELECT V_mean, V_slope, spike_rate, release_proxy, afferent_current "
            "FROM information_fiber WHERE cell_uid=?", (cell_uid,)
        ).fetchone()

        # Query spacetime cell
        cell = self.conn.execute(
            "SELECT x, y, z, normal_x, normal_y, normal_z, boundary_distance, support_radius "
            "FROM spacetime_cell WHERE cell_uid=?", (cell_uid,)
        ).fetchone()

        # Query transport support (average weight of connected edges)
        tce = self.conn.execute(
            "SELECT AVG(transport_weight) FROM transport_current_edge "
            "WHERE (from_cell_uid=? OR to_cell_uid=?) AND accepted=1",
            (cell_uid, cell_uid)
        ).fetchone()

        # Query occupancy
        occ = self.conn.execute(
            "SELECT AVG(membership_mass) FROM occupancy_measure WHERE cell_uid=?",
            (cell_uid,)
        ).fetchone()

        phi_info = abs(fib[0] or 0) + abs(fib[1] or 0) if fib else 0.0
        phi_signal = (fib[2] or 0) * 0.01 + abs(fib[3] or 0) if fib else 0.0
        phi_geo = 0.0
        if cell:
            # Local curvature proxy from normal variation
            phi_geo = abs(cell[3] or 0) + abs(cell[4] or 0)
            phi_boundary = cell[6] or 0.0
        else:
            phi_boundary = 0.0
        phi_transport = tce[0] or 0.0 if tce else 0.0
        phi_occupancy = occ[0] or 0.0 if occ else 0.0

        state_norm = math.sqrt(
            phi_info**2 + phi_geo**2 + phi_transport**2 +
            phi_boundary**2 + phi_signal**2 + phi_occupancy**2
        )

        state = {
            "phi_info": phi_info,
            "phi_geo": phi_geo,
            "phi_transport": phi_transport,
            "phi_boundary": phi_boundary,
            "phi_signal": phi_signal,
            "phi_occupancy": phi_occupancy,
            "state_norm": state_norm,
        }

        # Write to DB
        sid = _uid("sv")
        self.conn.execute(
            "INSERT INTO v361_variational_state_vector "
            "(state_id,run_id,window_id,cell_uid,phi_info,phi_geo,phi_transport,"
            "phi_boundary,phi_signal,phi_occupancy,state_norm,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, self.run_id, window_id, cell_uid,
             phi_info, phi_geo, phi_transport, phi_boundary,
             phi_signal, phi_occupancy, state_norm, _now()))

        return state

    def compute_lagrangian_terms(
        self,
        cell_uid: str,
        window_id: str,
        state: Dict[str, float],
    ) -> Dict[str, float]:
        """Decompose the Lagrangian into individual terms.

        V36.1 §4: L = sum_i alpha_i * L_i
        """
        terms = {
            "L_track": state["phi_transport"] * state["phi_occupancy"],
            "L_ledger": state["phi_info"] * 0.5,  # simplified proxy
            "L_xin": state["phi_info"] * state["phi_geo"],
            "L_boundary": state["phi_boundary"] ** 2,
            "L_signal": state["phi_signal"] * state["phi_transport"],
            "L_curvature": state["phi_geo"] ** 2,
        }

        for name, value in terms.items():
            coeff = self.weights.get(name, 1.0)
            weighted = coeff * value
            tid = _uid("lt")
            self.conn.execute(
                "INSERT INTO v361_lagrangian_term "
                "(term_id,run_id,window_id,cell_uid,term_name,term_value,"
                "coefficient,is_meta_proxy,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (tid, self.run_id, window_id, cell_uid, name,
                 weighted, coeff, 1, _now()))

        return terms

    def compute_el_residual(
        self,
        cell_uid: str,
        window_id: str,
        state: Dict[str, float],
        terms: Dict[str, float],
    ) -> Dict[str, float]:
        """Compute Euler-Lagrange residual and variational Xin.

        V36.1 §4.2:
          Xin_var = ||EL|| + omega_B * |B| + omega_C * CV
        """
        # EL residual: difference between kinetic and potential terms
        kinetic = sum(self.weights.get(k, 1.0) * v
                      for k, v in terms.items()
                      if k in ("L_track", "L_transport", "L_signal"))
        potential = sum(self.weights.get(k, 1.0) * v
                        for k, v in terms.items()
                        if k in ("L_boundary", "L_curvature", "L_xin"))

        el_norm = abs(kinetic - potential)
        boundary_term = state["phi_boundary"]

        # Constraint violation: occupancy should be bounded
        cv = max(0, state["phi_occupancy"] - 1.0)

        xin_var = el_norm + self.OMEGA_B * abs(boundary_term) + self.OMEGA_C * cv

        rid = _uid("elr")
        self.conn.execute(
            "INSERT INTO v361_euler_lagrange_residual "
            "(residual_id,run_id,window_id,cell_uid,el_residual_norm,"
            "boundary_term,constraint_violation,xin_variational,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (rid, self.run_id, window_id, cell_uid,
             el_norm, boundary_term, cv, xin_var, _now()))

        return {
            "el_residual_norm": el_norm,
            "boundary_term": boundary_term,
            "constraint_violation": cv,
            "xin_variational": xin_var,
        }

    def process_cell(
        self,
        cell_uid: str,
        window_id: str,
    ) -> Dict[str, Any]:
        """Full variational pipeline for a single cell."""
        state = self.build_state_vector(cell_uid, window_id)
        terms = self.compute_lagrangian_terms(cell_uid, window_id, state)
        residual = self.compute_el_residual(cell_uid, window_id, state, terms)

        # Also write to delta_xin_field
        fid = _uid("dxf")
        self.conn.execute(
            "INSERT INTO v36_delta_xin_field "
            "(field_id,run_id,cell_uid,stage_k,xin_value,xin_type,source_term,created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (fid, self.run_id, cell_uid, 0, residual["xin_variational"],
             "variational", "el_residual", _now()))

        return {"state": state, "terms": terms, "residual": residual}


# ═══════════════════════════════════════════════════════════════
# Information-Energy Metric Engine
# ═══════════════════════════════════════════════════════════════

class InformationEnergyMetricEngine:
    """Computes d_IE between cells.

    V36.1 §5:
      d_IE(a,b) = min over top-k admissible paths sum L_IE(e_i)

    Simplified to transport-weighted shortest path in the cell graph.

    V36 §4.4: mu_IE != real physics metric. This is a computational proxy.
    """

    def __init__(self, conn: "sqlite3.Connection", run_id: str):
        self.conn = conn
        self.run_id = run_id

    def compute_pairwise(
        self,
        cell_uid_a: str,
        cell_uid_b: str,
    ) -> Dict[str, Any]:
        """Compute d_IE between two cells using state vector distance.

        Simplified proxy: Euclidean distance in variational state space.
        """
        sv_a = self.conn.execute(
            "SELECT phi_info,phi_geo,phi_transport,phi_boundary,phi_signal,phi_occupancy "
            "FROM v361_variational_state_vector WHERE run_id=? AND cell_uid=? "
            "ORDER BY created_at DESC LIMIT 1",
            (self.run_id, cell_uid_a)
        ).fetchone()

        sv_b = self.conn.execute(
            "SELECT phi_info,phi_geo,phi_transport,phi_boundary,phi_signal,phi_occupancy "
            "FROM v361_variational_state_vector WHERE run_id=? AND cell_uid=? "
            "ORDER BY created_at DESC LIMIT 1",
            (self.run_id, cell_uid_b)
        ).fetchone()

        if not sv_a or not sv_b:
            return {"d_IE": float("inf"), "valid": False}

        # Euclidean distance in state space
        d_IE = math.sqrt(sum((a - b) ** 2 for a, b in zip(sv_a, sv_b)))

        mid = _uid("iem")
        self.conn.execute(
            "INSERT INTO v361_information_energy_metric "
            "(metric_id,run_id,cell_uid_a,cell_uid_b,d_IE,path_length,path_cost,"
            "is_physics_metric,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (mid, self.run_id, cell_uid_a, cell_uid_b, d_IE,
             1, d_IE, 0, _now()))  # is_physics_metric=0 enforced by schema

        return {"d_IE": d_IE, "valid": True, "metric_id": mid}

    def classify_relation(
        self,
        cell_uid_a: str,
        cell_uid_b: str,
        d_IE: float,
        d_IE_prev: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Classify the relation between two cells.

        V36.1 §6: Strictly read-only projection.
        """
        if d_IE_prev is not None:
            delta = d_IE - d_IE_prev
            if delta < -0.1:
                rel_type = "approaching"
            elif delta > 0.1:
                rel_type = "receding"
            elif abs(delta) < 0.01:
                rel_type = "stationary"
            else:
                rel_type = "oscillating"
        else:
            rel_type = "unknown"

        confidence = min(1.0, 1.0 / max(d_IE, 0.01))

        pid = _uid("rrp")
        self.conn.execute(
            "INSERT INTO v361_relation_readout_proxy "
            "(proxy_id,run_id,cell_uid_a,cell_uid_b,relation_type,"
            "d_IE_value,confidence,can_write_semantic_label,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (pid, self.run_id, cell_uid_a, cell_uid_b, rel_type,
             d_IE, confidence, 0, _now()))  # can_write_semantic_label=0 enforced

        return {
            "proxy_id": pid,
            "relation_type": rel_type,
            "d_IE": d_IE,
            "confidence": confidence,
        }
