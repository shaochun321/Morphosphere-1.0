"""SPMS Populator: Bridges existing V8 pipeline objects into SPMS tables.

V8.3 P3-P5: Translates PreNeuralPointSetSlice, SignalWindow, TransportEdge,
and PRDecompositionResult into SpacetimeCell, InformationFiber,
TransportCurrentEdge, OccupancyMeasure, and MaskingCounterevidenceRecord.

This is a write-time bridge, not a query-time converter. Once SPMS is populated,
all downstream operations (hypothesis, masking, maturity gate) operate on SPMS.
"""
import hashlib
import json
import uuid
from typing import Dict, List, Optional, Tuple

import numpy as np

from ...preneural.pointset_slice import PreNeuralPointSetSlice
from ...preneural.signal_window import SignalWindow
from ...preneural.geometry import GeometryNode
from ...preneural.transport.builder import TransportEdge as V8TransportEdge, TransportOperator
from ...stage2_object.decomposition.proposer import PRDecompositionResult
from ...contracts.clock import AnalysisWindow

from .core import (
    SpacetimeCell,
    InformationFiber,
    TransportCurrentEdge,
    OccupancyMeasure,
    MaskingCounterevidenceRecord,
    MASKING_TYPES,
)


class SPMSPopulator:
    """Populates SPMS tables from existing V8 pipeline outputs.

    Usage:
        pop = SPMSPopulator(run_id="run_001")
        cells, fibers = pop.populate_from_slice(slice, window)
        edges = pop.populate_transport(transport_op, cell_map)
        hypotheses, measures = pop.populate_hypotheses(decomp, cells)
        masking_records = pop.run_random_masking(hypothesis_id, cells, measures)
    """

    def __init__(self, run_id: str, calibration_profile: str = "default_v83"):
        self.run_id = run_id
        self.calibration_profile = calibration_profile
        # cell_uid lookup: (window_id, node_id) -> cell_uid
        self._cell_map: Dict[Tuple[str, int], str] = {}

    def populate_from_slice(
        self,
        sl: PreNeuralPointSetSlice,
        window: AnalysisWindow,
        stage_k: int = 0,
    ) -> Tuple[List[SpacetimeCell], List[InformationFiber]]:
        """Convert a PointSetSlice + its SignalWindows into SpacetimeCells + Fibers."""
        cells = []
        fibers = []

        for idx, node_id in enumerate(sl.geometry_node_ids):
            cell_uid = SpacetimeCell.generate_uid(self.run_id, window.window_id, node_id)
            self._cell_map[(window.window_id, node_id)] = cell_uid

            # Geometry
            if idx < len(sl.geometry_nodes):
                g = sl.geometry_nodes[idx]
                x, y, z = g.position
                nx, ny, nz = g.surface_normal
                bdist = g.boundary_distance
                sr = g.support_radius
                patches = json.dumps(g.source_patch_ids)
                neighbors = json.dumps(g.neighbor_ids)
            else:
                x, y, z = 0.0, 0.0, 0.0
                nx, ny, nz = 0.0, 0.0, 1.0
                bdist, sr = 0.0, 1.0
                patches, neighbors = "[]", "[]"

            cells.append(SpacetimeCell(
                cell_uid=cell_uid,
                run_id=self.run_id,
                stage_k=stage_k,
                window_id=window.window_id,
                node_id=node_id,
                clock_start=window.clock_start,
                clock_end=window.clock_end,
                x=x, y=y, z=z,
                normal_x=nx, normal_y=ny, normal_z=nz,
                boundary_distance=bdist,
                support_radius=sr,
                source_patch_ids_json=patches,
                topology_neighbors_json=neighbors,
                provenance_hash=sl.provenance_hash,
            ))

            # Fiber
            if idx < len(sl.signal_windows):
                sw = sl.signal_windows[idx]
                ref_json = json.dumps({"window_id": sw.window_id, "node_id": sw.node_id})
                fibers.append(InformationFiber(
                    fiber_id=InformationFiber.generate_id(cell_uid),
                    cell_uid=cell_uid,
                    V_mean=sw.V_mean,
                    V_slope=sw.V_slope,
                    release_proxy=sw.release_proxy,
                    afferent_current=sw.afferent_current,
                    spike_rate=sw.spike_rate,
                    spike_regularity=sw.spike_regularity,
                    timing_precision=sw.timing_precision,
                    adaptation_state=sw.adaptation_state,
                    source_signal_refs_json=ref_json,
                    calibration_profile=self.calibration_profile,
                ))

        return cells, fibers

    def populate_transport(
        self,
        transport_op: TransportOperator,
        from_window_id: str,
        to_window_id: str,
    ) -> List[TransportCurrentEdge]:
        """Convert V8 TransportOperator edges into SPMS TransportCurrentEdge rows."""
        edges = []
        for e in transport_op.edges:
            from_node = int(e.from_node_id)
            to_node = int(e.to_node_id)
            from_uid = self._cell_map.get((from_window_id, from_node))
            to_uid = self._cell_map.get((to_window_id, to_node))
            if not from_uid or not to_uid:
                continue

            edges.append(TransportCurrentEdge(
                edge_id=e.edge_id or f"tce_{uuid.uuid4().hex[:8]}",
                run_id=self.run_id,
                from_cell_uid=from_uid,
                to_cell_uid=to_uid,
                transport_weight=e.transport_weight,
                current_mass=e.transport_weight,
                geometry_cost=1.0 - e.geometry_similarity,
                normal_cost=1.0 - e.topology_similarity if e.topology_similarity > 0 else 0.0,
                boundary_cost=getattr(e, "boundary_cost", 0.0),
                signal_cost=getattr(e, "signal_drift", 1.0 - e.signal_similarity if e.signal_similarity > 0 else 0.0),
                source_patch_overlap=e.source_patch_overlap,
                fragility_penalty=0.0,
                accepted=bool(e.accepted),
                transport_variant="mainline" if e.accepted else "diagnostic_rejected_candidate",
                signal_drift=getattr(e, "signal_drift", 1.0 - e.signal_similarity),
                gating_failure_reason=getattr(e, "gating_failure_reason", None),
            ))

        return edges

    def populate_hypotheses_from_decomposition(
        self,
        decomp: PRDecompositionResult,
        window_id: str,
        stage_k: int = 0,
        threshold_p: float = 0.5,
        threshold_r: float = 0.3,
    ) -> Tuple[List[dict], List[OccupancyMeasure]]:
        """Generate object_hypothesis + occupancy_measure from P/R decomposition.

        Returns (hypotheses_as_dicts, occupancy_measures).
        Hypotheses are returned as dicts for DB insert since ObjectHypothesis
        is defined in the migration; full Pydantic model is in Batch 3.
        """
        hypotheses = []
        measures = []

        # P hypothesis
        p_hyp_id = f"hyp_p_{uuid.uuid4().hex[:8]}"
        p_nodes = [int(i) for i in range(len(decomp.E_P)) if decomp.E_P[i] > threshold_p]
        if p_nodes:
            hypotheses.append({
                "hypothesis_id": p_hyp_id,
                "hypothesis_type": "P_candidate",
                "stage_k": stage_k,
                "run_id": self.run_id,
                "status": "candidate",
                "member_cell_uids_json": json.dumps([
                    self._cell_map.get((window_id, n), f"unknown_{n}") for n in p_nodes
                ]),
                "support_score": float(np.mean(decomp.E_P[p_nodes])),
                "source_decomposition_ref": "P_m",
            })
            for n in p_nodes:
                cell_uid = self._cell_map.get((window_id, n), f"unknown_{n}")
                measures.append(OccupancyMeasure(
                    measure_id=f"occ_{uuid.uuid4().hex[:8]}",
                    hypothesis_id=p_hyp_id,
                    cell_uid=cell_uid,
                    membership_mass=float(decomp.E_P[n]),
                    transport_support=float(decomp.kappa[n]) if n < len(decomp.kappa) else 0.0,
                    signal_support=float(decomp.E_P[n]),
                    geometry_support=1.0,
                    core_margin_label="core" if decomp.E_P[n] > threshold_p * 1.5 else "margin",
                ))

        # R hypothesis
        r_hyp_id = f"hyp_r_{uuid.uuid4().hex[:8]}"
        r_nodes = [int(i) for i in range(len(decomp.E_R)) if decomp.E_R[i] > threshold_r]
        if r_nodes:
            hypotheses.append({
                "hypothesis_id": r_hyp_id,
                "hypothesis_type": "R_candidate",
                "stage_k": stage_k,
                "run_id": self.run_id,
                "status": "candidate",
                "member_cell_uids_json": json.dumps([
                    self._cell_map.get((window_id, n), f"unknown_{n}") for n in r_nodes
                ]),
                "support_score": float(np.mean(decomp.E_R[r_nodes])),
                "source_decomposition_ref": "R_m",
            })
            for n in r_nodes:
                cell_uid = self._cell_map.get((window_id, n), f"unknown_{n}")
                measures.append(OccupancyMeasure(
                    measure_id=f"occ_{uuid.uuid4().hex[:8]}",
                    hypothesis_id=r_hyp_id,
                    cell_uid=cell_uid,
                    membership_mass=float(decomp.E_R[n]),
                    signal_support=float(decomp.E_R[n]),
                    geometry_support=1.0,
                    core_margin_label="margin",
                ))

        return hypotheses, measures

    def run_random_masking(
        self,
        hypothesis_id: str,
        occupancy_measures: List[OccupancyMeasure],
        masking_strength: float = 0.3,
        seed: int = 42,
        origin_anchored: bool = False,
    ) -> MaskingCounterevidenceRecord:
        """V8.3 P5: Run a single random-node masking trial.

        Masks a fraction of cells and measures occupancy retention.
        """
        rng = np.random.RandomState(seed)
        n = len(occupancy_measures)
        if n == 0:
            return MaskingCounterevidenceRecord(
                record_id=f"mask_{uuid.uuid4().hex[:8]}",
                hypothesis_id=hypothesis_id,
                verdict="inconclusive",
            )

        # Base mass
        base_mass = sum(m.membership_mass for m in occupancy_measures)

        # Mask random subset
        n_mask = max(1, int(n * masking_strength))
        mask_indices = set(rng.choice(n, size=n_mask, replace=False))

        # Compute masked mass (remove masked cells)
        masked_mass = sum(
            m.membership_mass for i, m in enumerate(occupancy_measures)
            if i not in mask_indices
        )

        retention = masked_mass / base_mass if base_mass > 0 else 0.0

        # OriginAnchorBundle Invincibility (10x Survival Weight Boost)
        if origin_anchored:
            retention = min(1.0, retention * 10.0)

        # Verdict logic
        if retention > 0.8:
            verdict = "supports_confirmation"
        elif retention > 0.5:
            verdict = "weakens_confirmation"
        elif retention > 0.2:
            verdict = "inconclusive"
        else:
            verdict = "refutes_candidate"

        return MaskingCounterevidenceRecord(
            record_id=f"mask_{uuid.uuid4().hex[:8]}",
            hypothesis_id=hypothesis_id,
            masking_type="random_node",
            masking_strength=masking_strength,
            masked_fraction=n_mask / n,
            mask_specification_json=json.dumps({"masked_indices": [int(i) for i in sorted(mask_indices)]}),
            base_membership_mass=base_mass,
            masked_membership_mass=masked_mass,
            mass_retention=retention,
            classification_consistency=retention,
            trajectory_continuity=retention,
            verdict=verdict,
            run_id=self.run_id,
        )
