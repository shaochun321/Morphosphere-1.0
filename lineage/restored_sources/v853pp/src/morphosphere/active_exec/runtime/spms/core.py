"""SPMS core dataclasses: SpacetimeCell, InformationFiber, TransportCurrentEdge,
OccupancyMeasure, MaskingCounterevidenceRecord.

V8.3 §5: These are the five minimal SPMS tables that give P/R freezing
its process-measure substrate.

Design principles:
  - SpacetimeCell is the coordinate anchor — every other SPMS object references it.
  - InformationFiber is the signal state ATTACHED to a cell, never floating.
  - TransportCurrentEdge is a directed edge with full cost breakdown.
  - OccupancyMeasure records how much a hypothesis occupies a spacetime cell.
  - MaskingCounterevidenceRecord is the P/R freeze hard gate.
"""
import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════
#  Plane 1: Spacetime Coordinate Plane
# ═══════════════════════════════════════════════════════════════════════

class SpacetimeCell(BaseModel):
    """V8.3 §5.2: Unified spacetime coordinate anchor.

    All information fibers, transport currents, occupancy measures, and
    boundary records reference this cell via cell_uid.
    """
    cell_uid: str = Field(..., description="Globally unique cell identifier")
    run_id: str = Field(..., description="Run identifier")
    stage_k: int = Field(default=0, description="Stage index")
    window_id: str = Field(..., description="Analysis window ID")
    node_id: int = Field(..., description="Node index within window")
    clock_start: int = Field(default=0, description="Start clock_n")
    clock_end: int = Field(default=0, description="End clock_n")
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    z: float = Field(default=0.0)
    normal_x: float = Field(default=0.0)
    normal_y: float = Field(default=0.0)
    normal_z: float = Field(default=1.0)
    boundary_distance: float = Field(default=0.0)
    support_radius: float = Field(default=1.0)
    source_patch_ids_json: str = Field(default="[]")
    topology_neighbors_json: str = Field(default="[]")
    coordinate_frame_id: str = Field(default="default")
    provenance_hash: str = Field(default="")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SpacetimeCell":
        return cls.model_validate(row)

    @staticmethod
    def generate_uid(run_id: str, window_id: str, node_id: int) -> str:
        h = hashlib.sha256(f"{run_id}:{window_id}:{node_id}".encode()).hexdigest()[:12]
        return f"cell_{h}"


# ═══════════════════════════════════════════════════════════════════════
#  Plane 2: Information Fiber Plane
# ═══════════════════════════════════════════════════════════════════════

class InformationFiber(BaseModel):
    """V8.3 §5.3: Signal state as fiber attached to spacetime cell.

    Information is never floating — it must reference a cell_uid.
    """
    fiber_id: str = Field(..., description="Unique fiber ID")
    cell_uid: str = Field(..., description="Reference to spacetime_cell")
    V_mean: float = Field(default=0.0)
    V_slope: float = Field(default=0.0)
    release_proxy: float = Field(default=0.0)
    afferent_current: float = Field(default=0.0)
    spike_rate: float = Field(default=0.0)
    spike_regularity: float = Field(default=0.0)
    timing_precision: float = Field(default=0.0)
    adaptation_state: float = Field(default=0.0)
    signal_uncertainty: float = Field(default=0.0)
    compression_loss: float = Field(default=0.0)
    source_signal_refs_json: str = Field(default="[]")
    calibration_profile: str = Field(default="default_v83")
    provenance_hash: str = Field(default="")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "InformationFiber":
        return cls.model_validate(row)

    @staticmethod
    def generate_id(cell_uid: str) -> str:
        return f"fiber_{cell_uid[5:]}"  # Strip "cell_" prefix


# ═══════════════════════════════════════════════════════════════════════
#  Plane 3: Transport Current Plane
# ═══════════════════════════════════════════════════════════════════════

class TransportCurrentEdge(BaseModel):
    """V8.3 §5.4: Per-edge transport with full cost breakdown.

    Replaces the dense mapping_matrix approach with traceable edges.
    Each accepted edge has from/to spacetime cells and cost components.
    """
    edge_id: str = Field(..., description="Unique edge ID")
    run_id: str = Field(..., description="Run identifier")
    from_cell_uid: str = Field(..., description="Source spacetime cell")
    to_cell_uid: str = Field(..., description="Target spacetime cell")
    transport_weight: float = Field(default=1.0)
    current_mass: float = Field(default=1.0)
    geometry_cost: float = Field(default=0.0)
    normal_cost: float = Field(default=0.0)
    boundary_cost: float = Field(default=0.0)
    signal_cost: float = Field(default=0.0)
    source_patch_overlap: float = Field(default=0.0)
    fragility_penalty: float = Field(default=0.0)
    accepted: bool = Field(default=True)
    transport_variant: str = Field(default="mainline")
    cycle_consistency_local: float = Field(default=0.0)
    boundary_crossing_penalty: float = Field(default=0.0)
    signal_drift: float = Field(default=0.0)
    gating_failure_reason: Optional[str] = Field(default=None)
    provenance_hash: str = Field(default="")

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        d["accepted"] = int(d["accepted"])
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "TransportCurrentEdge":
        if "accepted" in row:
            row["accepted"] = bool(row["accepted"])
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  Plane 5: Occupancy Measure Plane
# ═══════════════════════════════════════════════════════════════════════

class OccupancyMeasure(BaseModel):
    """V8.3 §5.6: Empirical occupancy measure for hypothesis on spacetime cell.

    This upgrades P/R from bare "weight" to a full process measure with
    multi-run statistics, masking survival, and replay support breakdown.
    """
    measure_id: str = Field(..., description="Unique measure ID")
    hypothesis_id: str = Field(..., description="Reference to object_hypothesis")
    cell_uid: str = Field(..., description="Reference to spacetime_cell")
    # Mass
    membership_mass: float = Field(default=0.0)
    membership_entropy: float = Field(default=0.0)
    occupancy_rank: int = Field(default=0)
    # Sampling context
    run_count: int = Field(default=1)
    window_count: int = Field(default=1)
    masking_trial_count: int = Field(default=0)
    replay_trial_count: int = Field(default=0)
    boundary_variant_count: int = Field(default=0)
    # Support breakdown
    transport_support: float = Field(default=0.0)
    signal_support: float = Field(default=0.0)
    geometry_support: float = Field(default=0.0)
    masking_support: float = Field(default=0.0)
    replay_support: float = Field(default=0.0)
    boundary_support: float = Field(default=0.0)
    # Counterevidence
    counterevidence_mass: float = Field(default=0.0)
    artifact_penalty: float = Field(default=0.0)
    # Classification
    core_margin_label: str = Field(default="unknown", description="core/margin/boundary/unknown")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OccupancyMeasure":
        return cls.model_validate(row)


# ═══════════════════════════════════════════════════════════════════════
#  Masking Counterevidence
# ═══════════════════════════════════════════════════════════════════════

MASKING_TYPES = [
    "random_node", "random_edge", "signal_dimension",
    "source_patch", "topology_patch", "boundary_region",
    "temporal_window", "mixed",
]

# V8.3 legacy verdicts (kept for backward compatibility)
MASKING_VERDICTS = [
    "supports_freeze", "weakens_freeze", "refutes_freeze", "inconclusive",
]

# V8.5 extended verdicts (§5.2)
MASKING_VERDICTS_V85 = [
    "supports_confirmation", "weakens_confirmation", "refutes_candidate",
    "inconclusive",
    "escalate_to_replay", "escalate_to_boundary",
    "downgrade_to_xi", "trigger_emergence_alert",
]


class MaskingCounterevidenceRecord(BaseModel):
    """V8.5 §5 / V8.3 §7: Masking counterevidence — embedded INTO confirmation process.

    V8.5 upgrade: masking is no longer a post-P/R audit step. It is embedded
    into the P/R confirmation graph. Extended fields link masking to O-level
    associations and confirmation graph state transitions.
    """
    record_id: str = Field(..., description="Unique record ID")
    hypothesis_id: str = Field(..., description="Reference to object_hypothesis")
    masking_type: str = Field(default="random_node", description="Type of masking applied")
    masking_strength: float = Field(default=0.5, description="Fraction of input masked")
    masked_fraction: float = Field(default=0.0, description="Actual fraction masked")
    mask_specification_json: str = Field(default="{}", description="Detailed mask config")
    # Results
    base_membership_mass: float = Field(default=0.0, description="Pre-mask occupancy")
    masked_membership_mass: float = Field(default=0.0, description="Post-mask occupancy")
    mass_retention: float = Field(default=0.0, description="masked_mass / base_mass")
    classification_consistency: float = Field(default=0.0, description="P/R label stability")
    trajectory_continuity: float = Field(default=0.0, description="Transport chain survival")
    # Verdict (V8.5 extended)
    verdict: str = Field(default="inconclusive", description="V8.5 masking verdict")
    run_id: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    # ── V8.5 §5.3 New Fields ──────────────────────────────────────────
    # O-level associations (masking must relate to O, not just P/R)
    o_field_id: Optional[str] = Field(default=None, description="O field surface ID")
    o_candidate_id: Optional[str] = Field(default=None, description="O candidate surface ID")
    o_candidate_lineage_id: Optional[str] = Field(default=None, description="O candidate lineage")
    p_candidate_id: Optional[str] = Field(default=None, description="P candidate ID if applicable")
    r_candidate_id: Optional[str] = Field(default=None, description="R candidate ID if applicable")
    xi_candidate_id: Optional[str] = Field(default=None, description="Xi candidate ID if applicable")
    # Confirmation graph state tracking
    confirmation_state_before: Optional[str] = Field(default=None, description="Graph node before masking")
    confirmation_state_after: Optional[str] = Field(default=None, description="Graph node after masking")
    # Resource optimization
    recommended_compute_tier: Optional[str] = Field(default=None, description="Compute tier recommendation")
    resource_saving_reason: Optional[str] = Field(default=None, description="Why early rejection saves resources")
    # Cross-references
    ledger_alignment_report_id: Optional[str] = Field(default=None)
    emergence_alert_id: Optional[str] = Field(default=None)

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "MaskingCounterevidenceRecord":
        return cls.model_validate(row)
