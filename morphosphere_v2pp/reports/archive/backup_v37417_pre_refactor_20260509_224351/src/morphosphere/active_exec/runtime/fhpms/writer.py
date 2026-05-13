"""
Minimal Write/Read Proxy for HG-FHPMS (Hebbian-Guided Fiber-Hypergraph Potential Memory Store)
V37.4.12 Blueprint implementation.
"""
from typing import Dict, Any, List, Optional
import sqlite3
import uuid
import datetime
import json
import math

def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def _jdump(obj: Any) -> str:
    return json.dumps(obj) if obj else "[]"

class FHPMSWriter:
    """
    Proxy for writing process traces, hyperedge bindings, reprojection traces,
    and Hebbian association weights in HG-FHPMS.
    """
    def __init__(self, conn: sqlite3.Connection, run_id: str):
        self.conn = conn
        self.run_id = run_id

    def write_process_trace(self,
                            process_window_id: str,
                            time_start: float,
                            time_end: float,
                            envelope_ref: str,
                            origin_anchor_refs: List[str],
                            p_measure: float = 0.0,
                            r_measure: float = 0.0,
                            x_measure: float = 0.0,
                            u_measure: float = 0.0) -> Dict[str, str]:
        """
        Write a complete trace into FHPMS, forming a block, fiber state, potential, and origin anchor.
        """
        # 1. Create Origin Anchor Trace
        anchor_id = _uid("oat")
        self.conn.execute(
            "INSERT INTO fhpms_origin_anchor_trace "
            "(origin_anchor_id, raw_event_refs_json, external_envelope_refs_json, reprojection_status, created_at) "
            "VALUES (?,?,?,?,?)",
            (anchor_id, _jdump(origin_anchor_refs), _jdump([envelope_ref]), "coarse_proxy", _now())
        )

        # 2. Create Process Block
        block_id = _uid("blk")
        self.conn.execute(
            "INSERT INTO fhpms_spacetime_process_block "
            "(block_id, process_window_id, time_start, time_end, external_envelope_ref, origin_anchor_id, projection_granularity, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (block_id, process_window_id, time_start, time_end, envelope_ref, anchor_id, "window_level", _now())
        )

        # 3. Create PRX Fiber State
        fs_id = _uid("fs")
        self.conn.execute(
            "INSERT INTO fhpms_prx_fiber_state "
            "(fiber_state_id, block_id, p_measure, r_measure, x_measure, u_measure, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (fs_id, block_id, p_measure, r_measure, x_measure, u_measure, _now())
        )

        # 4. Create Initial Potential (all 7 terms from v1.1 §5)
        pot_id = _uid("pot")
        phi_d = 0.1 * (time_end - time_start)
        phi_p = p_measure * 0.5
        phi_r = r_measure * 0.3
        phi_x = x_measure * 0.1
        phi_l = 0.05  # ledger sync baseline
        phi_m = 0.02  # masking baseline
        phi_h = 0.03  # hyperedge baseline
        self.conn.execute(
            "INSERT INTO fhpms_distance_spacetime_potential "
            "(potential_id, block_id, phi_d, phi_p, phi_r, phi_x, phi_l, phi_m, phi_h, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (pot_id, block_id, phi_d, phi_p, phi_r, phi_x, phi_l, phi_m, phi_h, _now())
        )

        return {
            "block_id": block_id,
            "fiber_state_id": fs_id,
            "potential_id": pot_id,
            "origin_anchor_id": anchor_id
        }

    def write_hyperedge_binding(self,
                                block_refs: List[str],
                                p_anchor_refs: List[str],
                                r_band_refs: List[str],
                                xin_carrier_refs: List[str],
                                envelope_refs: List[str],
                                origin_anchor_refs: List[str],
                                binding_strength: float = 1.0) -> str:
        """Write a hyperedge binding connecting multiple blocks via fiber measures.
        v1.1 §3: Hyperedge is the high-order binding in HG-FHPMS.
        """
        he_id = _uid("fhe")
        self.conn.execute(
            "INSERT INTO fhpms_hyperedge_fiber_binding "
            "(hyperedge_id, block_refs_json, p_anchor_refs_json, r_band_refs_json, "
            "xin_carrier_refs_json, ledger_refs_json, masking_refs_json, attention_refs_json, "
            "envelope_refs_json, origin_anchor_refs_json, binding_strength, arity, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (he_id, _jdump(block_refs), _jdump(p_anchor_refs), _jdump(r_band_refs),
             _jdump(xin_carrier_refs), _jdump([]), _jdump([]), _jdump([]),
             _jdump(envelope_refs), _jdump(origin_anchor_refs),
             binding_strength, len(block_refs), _now())
        )
        return he_id

    def write_reprojection_trace(self,
                                 block_id: str,
                                 origin_anchor_id: str,
                                 t_start: float,
                                 t_end: float,
                                 x_proxy: float,
                                 y_proxy: float,
                                 z_proxy: float,
                                 coordinate_frame: str = "adapter_local",
                                 projection_confidence: float = 0.5,
                                 granularity: str = "coarse_window_level") -> str:
        """Write a coarse reprojection trace mapping FHPMS block back to bottom-layer coordinates.
        v1.1 §11: Coarse reprojection is the current degradation target.
        """
        trace_id = _uid("rpt")
        self.conn.execute(
            "INSERT INTO fhpms_reprojection_trace "
            "(trace_id, block_id, origin_anchor_id, t_start, t_end, "
            "x_proxy, y_proxy, z_proxy, coordinate_frame, "
            "projection_confidence, granularity_level, loss_reason, created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (trace_id, block_id, origin_anchor_id, t_start, t_end,
             x_proxy, y_proxy, z_proxy, coordinate_frame,
             projection_confidence, granularity, "coarse_projection_only", _now())
        )
        return trace_id

    def write_hebbian_weight(self,
                             from_entity_id: str,
                             to_entity_id: str,
                             association_type: str,
                             weight_value: float,
                             gamma_strength: float = 1.0,
                             envelope_compatible: bool = True,
                             writeback_allowed: bool = False) -> Optional[str]:
        """Write a Hebbian association weight between two FHPMS entities.
        v1.1 §6: Gate conditions:
          G_ij = 1[Gamma > Gamma_crit] * 1[envelope_compatible] * 1[writeback_allowed=0]
        Unresolved Xin (u > theta_U) blocks consolidation.
        """
        GAMMA_CRIT = 0.5
        # Gate check
        gate = (gamma_strength > GAMMA_CRIT) and envelope_compatible and (not writeback_allowed)
        if not gate:
            return None

        w_id = _uid("heb")
        gate_status = f"gamma={gamma_strength:.3f},env={envelope_compatible},wb={writeback_allowed}"
        self.conn.execute(
            "INSERT INTO fhpms_hebbian_association_weight "
            "(weight_id, from_entity_id, to_entity_id, association_type, "
            "weight_value, hebbian_gate_status, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (w_id, from_entity_id, to_entity_id, association_type,
             weight_value, gate_status, _now())
        )
        return w_id

    def read_potential_guided(self, query_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Softmax potential-guided retrieval skeleton.
        For now, just returns blocks ordered by a proxy potential value.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT b.block_id, p.phi_p, p.phi_r, p.phi_x "
            "FROM fhpms_spacetime_process_block b "
            "JOIN fhpms_distance_spacetime_potential p ON b.block_id = p.block_id "
            "ORDER BY (p.phi_p + p.phi_r) DESC LIMIT 10"
        )
        results = [{"block_id": r[0], "phi_p": r[1], "phi_r": r[2], "phi_x": r[3]} for r in cursor.fetchall()]
        return results
