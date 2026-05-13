"""SPMS Runtime Binder: Connects PreNeural pipeline output to SPMS storage.

V8.3 §5 / V8.5 §8: The binding layer that writes PreNeuralPointSetSlice,
SignalWindow, and TransportOperator data into the SPMS five-table core:
  spacetime_cell, information_fiber, spacetime_fiber_binding,
  transport_current_edge, object_hypothesis + occupancy_measure.

Hard rules (v8.5 §8.4):
  - Any query using information_fiber must trace back to spacetime_cell + binding.
  - Transport edges must reference their endpoint bindings, not just node IDs.
  - P/R/Xi candidates must trace back to at least one spacetime_fiber_binding.
"""
from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3
    from ...preneural.pointset_slice import PreNeuralPointSetSlice
    from ...preneural.transport.builder import TransportOperator
    from ...contracts.clock import AnalysisWindow

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _jdump(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class SPMSBinder:
    """Binds PreNeural pipeline outputs to SPMS tables.

    Usage:
        binder = SPMSBinder(conn, run_id, calibration_profile="v85_diagnostic")
        cell_map = binder.bind_slice(slice, window)
        binder.bind_transport(transport_op, prev_cell_map, curr_cell_map)
    """

    def __init__(
        self,
        conn: "sqlite3.Connection",
        run_id: str,
        calibration_profile: str = "diagnostic",
        coordinate_frame_id: str = "preneural_local",
    ):
        self.conn = conn
        self.run_id = run_id
        self.calibration_profile = calibration_profile
        self.coordinate_frame_id = coordinate_frame_id

    def bind_slice(
        self,
        pslice: "PreNeuralPointSetSlice",
        window: Optional["AnalysisWindow"] = None,
        stage_k: Optional[int] = None,
    ) -> Dict[int, str]:
        """Write spacetime_cell + information_fiber + spacetime_fiber_binding.

        Returns:
            node_id → cell_uid mapping for transport binding.
        """
        k = stage_k if stage_k is not None else pslice.stage_k
        win_id = pslice.window_id
        clock_start = window.clock_start if window else k
        clock_end = window.clock_end if window else k + 1

        node_to_uid: Dict[int, str] = {}

        for idx, node_id in enumerate(pslice.geometry_node_ids):
            geo = pslice.geometry_nodes[idx] if idx < len(pslice.geometry_nodes) else None
            cell_uid = getattr(geo, "uid", f"sc_{self.run_id[:8]}_{k}_{node_id}")
            node_to_uid[node_id] = cell_uid

            # --- Geometry ---
            if geo:
                x, y, z = geo.position
                nx, ny, nz = geo.surface_normal
                bdist = geo.boundary_distance
                srad = geo.support_radius
                neighbors = geo.neighbor_ids
                patch_ids = geo.source_patch_ids
            else:
                x, y, z = 0.0, 0.0, 0.0
                nx, ny, nz = 0.0, 0.0, 1.0
                bdist, srad = 0.0, 1.0
                neighbors, patch_ids = [], [node_id]

            # --- Signal ---
            sig = pslice.signal_windows[idx] if idx < len(pslice.signal_windows) else None
            V_mean = sig.V_mean if sig else 0.0
            V_slope = sig.V_slope if sig else 0.0
            release_proxy = sig.release_proxy if sig else 0.0
            afferent_current = sig.afferent_current if sig else 0.0
            spike_rate = sig.spike_rate if sig else 0.0
            spike_regularity = sig.spike_regularity if sig else 0.0
            timing_precision = sig.timing_precision if sig else 0.0
            adaptation_state = sig.adaptation_state if sig else 0.0
            signal_uncertainty = 0.0

            # Provenance
            prov_raw = f"{self.run_id}:{k}:{node_id}:{V_mean:.6f}:{x:.4f}"
            prov_hash = hashlib.sha256(prov_raw.encode()).hexdigest()[:16]

            # Signal source refs
            sig_ref = {"window_id": win_id, "node_id": node_id}

            # === spacetime_cell ===
            self.conn.execute(
                "INSERT INTO spacetime_cell "
                "(cell_uid,run_id,stage_k,window_id,node_id,clock_start,clock_end,"
                "x,y,z,normal_x,normal_y,normal_z,boundary_distance,support_radius,"
                "source_patch_ids_json,topology_neighbors_json,coordinate_frame_id,"
                "provenance_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (cell_uid, self.run_id, k, win_id, node_id, clock_start, clock_end,
                 x, y, z, nx, ny, nz, bdist, srad,
                 _jdump(patch_ids), _jdump(neighbors),
                 self.coordinate_frame_id, prov_hash))

            # === information_fiber ===
            fiber_id = f"fib_{cell_uid}"
            self.conn.execute(
                "INSERT INTO information_fiber "
                "(fiber_id,cell_uid,V_mean,V_slope,release_proxy,afferent_current,"
                "spike_rate,spike_regularity,timing_precision,adaptation_state,"
                "signal_uncertainty,compression_loss,source_signal_refs_json,"
                "calibration_profile,provenance_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (fiber_id, cell_uid, V_mean, V_slope, release_proxy, afferent_current,
                 spike_rate, spike_regularity, timing_precision, adaptation_state,
                 signal_uncertainty, 0.0, _jdump(sig_ref),
                 self.calibration_profile, prov_hash))

            # === spacetime_fiber_binding (v8.5 §8.2) ===
            binding_id = f"bind_{cell_uid}"
            source_cell_ids = geo.source_patch_ids if geo else [node_id]
            binding_type = "direct" if geo and geo.position != (0.0, 0.0, 0.0) else "proxy"
            self.conn.execute(
                "INSERT INTO spacetime_fiber_binding "
                "(binding_id,run_id,clock_n,window_id,spacetime_cell_id,"
                "information_fiber_id,source_cell_ids_json,source_patch_ids_json,"
                "binding_type,calibration_profile,provenance_hash) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (binding_id, self.run_id, k, win_id, cell_uid, fiber_id,
                 _jdump(source_cell_ids), _jdump(patch_ids),
                 binding_type, self.calibration_profile, prov_hash))

        return node_to_uid

    def bind_transport(
        self,
        transport_op: "TransportOperator",
        prev_cell_map: Dict[int, str],
        curr_cell_map: Dict[int, str],
    ) -> int:
        """Write transport_current_edge rows from a TransportOperator.

        Args:
            transport_op: The TransportOperator from TransportBuilder.
            prev_cell_map: node_id → cell_uid for the source slice.
            curr_cell_map: node_id → cell_uid for the target slice.

        Returns:
            Number of edges written.
        """
        written = 0
        for edge in transport_op.edges:
            from_node = int(edge.from_node_id)
            to_node = int(edge.to_node_id)
            from_uid = prev_cell_map.get(from_node, f"unknown_{from_node}")
            to_uid = curr_cell_map.get(to_node, f"unknown_{to_node}")

            edge_id = edge.edge_id or _uid("tce")
            prov = f"tp_{from_node}_{to_node}_{edge.cost:.4f}"

            self.conn.execute(
                "INSERT INTO transport_current_edge "
                "(edge_id,run_id,from_cell_uid,to_cell_uid,transport_weight,"
                "current_mass,geometry_cost,normal_cost,boundary_cost,signal_cost,"
                "source_patch_overlap,fragility_penalty,accepted,transport_variant,"
                "cycle_consistency_local,boundary_crossing_penalty,signal_drift,"
                "gating_failure_reason,provenance_hash,total_cost) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (edge_id, self.run_id, from_uid, to_uid,
                 edge.transport_weight, edge.transport_weight,
                 edge.geometry_similarity, edge.topology_similarity,
                 edge.boundary_cost, edge.signal_drift,
                 edge.source_patch_overlap, 0.0,
                 1 if edge.accepted else 0,
                 "mainline" if edge.accepted else "rejected",
                 1.0 if edge.accepted else 0.0,
                 edge.boundary_cost, edge.signal_drift,
                 edge.gating_failure_reason, prov, edge.cost))
            written += 1
        return written

    def bind_hypothesis(
        self,
        hypothesis_type: str,
        stage_k: int,
        member_cell_uids: List[str],
        support_score: float,
        spatial_support: Optional[List[str]] = None,
        temporal_support: Optional[List[str]] = None,
    ) -> str:
        """Write an object_hypothesis and its occupancy measures.

        Returns:
            hypothesis_id
        """
        hid = _uid(f"hyp_{hypothesis_type[0].lower()}")

        self.conn.execute(
            "INSERT INTO object_hypothesis "
            "(hypothesis_id,hypothesis_type,stage_k,run_id,status,"
            "member_cell_uids_json,spatial_support_json,temporal_support_json,"
            "support_score,source_decomposition_ref) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (hid, hypothesis_type, stage_k, self.run_id, "candidate",
             _jdump(member_cell_uids),
             _jdump(spatial_support or member_cell_uids),
             _jdump(temporal_support or []),
             support_score, "spms_binder"))

        # occupancy measures for each member cell
        for i, uid in enumerate(member_cell_uids):
            mass = max(0.01, support_score - 0.02 * i)
            self.conn.execute(
                "INSERT INTO occupancy_measure "
                "(measure_id,hypothesis_id,cell_uid,membership_mass,"
                "transport_support,signal_support,geometry_support,"
                "masking_support,replay_support,core_margin_label) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (_uid("occ"), hid, uid, mass,
                 0.5, 0.5, 0.5, 0.0, 0.0,
                 "core" if i < len(member_cell_uids) // 2 else "margin"))

        return hid

    def verify_integrity(self) -> Dict[str, Any]:
        """V8.5 §8.3-8.4 integrity checks.

        Returns dict with check results.
        """
        results = {}

        # Check 1: No orphan fibers
        orphan_fibers = self.conn.execute(
            "SELECT COUNT(*) FROM information_fiber "
            "WHERE cell_uid NOT IN (SELECT cell_uid FROM spacetime_cell)"
        ).fetchone()[0]
        results["orphan_fibers"] = orphan_fibers

        # Check 2: No orphan bindings
        orphan_bindings = self.conn.execute(
            "SELECT COUNT(*) FROM spacetime_fiber_binding "
            "WHERE spacetime_cell_id NOT IN (SELECT cell_uid FROM spacetime_cell)"
        ).fetchone()[0]
        results["orphan_bindings"] = orphan_bindings

        # Check 3: Every fiber has a binding
        unbound_fibers = self.conn.execute(
            "SELECT COUNT(*) FROM information_fiber f "
            "WHERE NOT EXISTS (SELECT 1 FROM spacetime_fiber_binding b "
            "WHERE b.information_fiber_id = f.fiber_id)"
        ).fetchone()[0]
        results["unbound_fibers"] = unbound_fibers

        # Check 4: Transport edges reference valid cells
        invalid_transport = self.conn.execute(
            "SELECT COUNT(*) FROM transport_current_edge "
            "WHERE from_cell_uid NOT IN (SELECT cell_uid FROM spacetime_cell) "
            "OR to_cell_uid NOT IN (SELECT cell_uid FROM spacetime_cell)"
        ).fetchone()[0]
        results["invalid_transport_refs"] = invalid_transport

        results["all_pass"] = all(v == 0 for v in results.values())
        return results
