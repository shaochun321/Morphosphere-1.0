# Tags: [CORE_SCHEMA][CORE_RUNTIME][ORIGIN][VERSIONED]
# Role: Origin anchor bundle and recursive transition records.
# Must Not: Import semantic_readout or legacy modules.
# Producers: decomposition pipeline
# Consumers: family_surface, replay, ledger
"""Origin + Transition + T_seed — recursive object system (v5 P08-P09).

OriginAnchorBundle: Multi-evidence, multi-window convergence anchor.
  NOT a geometric center or a peak-value point.

RecursiveTransitionRecord: Records T_k → O_k → P/R → T_seed chain.

TSeedReplayPacket: Replay seed for the next recursive stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid


@dataclass
class OriginAnchorBundle:
    """Origin anchor bundle (v5 §P09).

    An origin is NOT a geometric center or maximum-value point.
    It must be a multi-evidence, multi-window convergence of
    supporting P bands, provenance rows, and behavioral references.

    Attributes:
        origin_id: Unique identifier
        supporting_p_ids: P-band records that support this origin
        provenance_rows: Provenance chain entries
        temporal_window: Clock range this origin spans
        observability_score: How observable is this origin
        stability_score: How stable across perturbations
    """
    origin_id: str = ""
    supporting_p_ids: list[str] = field(default_factory=list)
    provenance_rows: list[str] = field(default_factory=list)
    behavior_refs: list[str] = field(default_factory=list)
    masking_refs: list[str] = field(default_factory=list)
    temporal_window: tuple[int, int] = (0, 0)  # (clock_start, clock_end)
    observability_score: float = 0.0
    stability_score: float = 0.0

    @property
    def num_supporting_bands(self) -> int:
        return len(self.supporting_p_ids)

    def is_well_supported(self, min_bands: int = 2) -> bool:
        """Check if the origin has sufficient supporting evidence."""
        return self.num_supporting_bands >= min_bands

    def to_dict(self) -> dict[str, Any]:
        return {
            "origin_id": self.origin_id,
            "supporting_p_ids": list(self.supporting_p_ids),
            "provenance_rows": list(self.provenance_rows),
            "behavior_refs": list(self.behavior_refs),
            "masking_refs": list(self.masking_refs),
            "temporal_window": list(self.temporal_window),
            "observability_score": self.observability_score,
            "stability_score": self.stability_score,
            "num_supporting_bands": self.num_supporting_bands,
            "well_supported": self.is_well_supported(),
        }

    @classmethod
    def create(cls, **kwargs: Any) -> "OriginAnchorBundle":
        if "origin_id" not in kwargs or not kwargs["origin_id"]:
            kwargs["origin_id"] = f"omega_{uuid.uuid4().hex[:8]}"
        return cls(**kwargs)


@dataclass
class RecursiveTransitionRecord:
    """Recursive transition record (v5 §P08).

    Records the complete transition chain:
        T_k → O_k → P_k/R_k → OccupancyState → T_seed

    This is the formal record of one recursive stage.
    """
    transition_id: str = ""
    from_stage_k: int = 0
    to_stage_kplus1: int = 0

    # Summary of each transformation step
    t_to_o_summary: str = ""
    o_to_p_summary: str = ""
    o_to_r_summary: str = ""
    p_to_tseed_summary: str = ""

    # References
    triggering_r_ids: list[str] = field(default_factory=list)
    source_p_ids: list[str] = field(default_factory=list)
    origin_id: str = ""
    seed_id: str = ""

    # Metrics
    transition_confidence: float = 0.0
    continuity_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "from_stage_k": self.from_stage_k,
            "to_stage_kplus1": self.to_stage_kplus1,
            "t_to_o_summary": self.t_to_o_summary,
            "o_to_p_summary": self.o_to_p_summary,
            "o_to_r_summary": self.o_to_r_summary,
            "p_to_tseed_summary": self.p_to_tseed_summary,
            "triggering_r_ids": list(self.triggering_r_ids),
            "source_p_ids": list(self.source_p_ids),
            "origin_id": self.origin_id,
            "seed_id": self.seed_id,
            "transition_confidence": self.transition_confidence,
            "continuity_score": self.continuity_score,
        }

    @classmethod
    def create(cls, **kwargs: Any) -> "RecursiveTransitionRecord":
        if "transition_id" not in kwargs or not kwargs["transition_id"]:
            kwargs["transition_id"] = f"tr_{uuid.uuid4().hex[:8]}"
        return cls(**kwargs)


@dataclass
class TSeedReplayPacket:
    """T_seed replay packet (v5 §P09).

    A replay seed derived from the current stage's P/R decomposition,
    defining the allowed drive envelope and expected region for the
    next recursive stage.

    P_k → T_seed → T_{k+1}
    """
    seed_id: str = ""
    source_p_ids: list[str] = field(default_factory=list)
    source_r_ids: list[str] = field(default_factory=list)
    allowed_drive_envelope: str = ""
    expected_region: str = ""
    clock_window: tuple[int, int] = (0, 0)  # target clock range

    # Constraints for the next stage
    initial_state_hint: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "seed_id": self.seed_id,
            "source_p_ids": list(self.source_p_ids),
            "source_r_ids": list(self.source_r_ids),
            "allowed_drive_envelope": self.allowed_drive_envelope,
            "expected_region": self.expected_region,
            "clock_window": list(self.clock_window),
            "has_initial_hint": bool(self.initial_state_hint),
        }

    @classmethod
    def create(cls, **kwargs: Any) -> "TSeedReplayPacket":
        if "seed_id" not in kwargs or not kwargs["seed_id"]:
            kwargs["seed_id"] = f"ts_{uuid.uuid4().hex[:8]}"
        return cls(**kwargs)


def build_transition_record(
    *,
    stage_k: int,
    p_ids: list[str],
    r_ids: list[str],
    origin_id: str = "",
    seed: TSeedReplayPacket | None = None,
) -> RecursiveTransitionRecord:
    """Build a transition record from stage components."""
    record = RecursiveTransitionRecord.create(
        from_stage_k=stage_k,
        to_stage_kplus1=stage_k + 1,
        source_p_ids=p_ids,
        triggering_r_ids=r_ids,
        origin_id=origin_id,
        seed_id=seed.seed_id if seed else "",
        t_to_o_summary=f"Stage {stage_k}: T→O via observation field",
        o_to_p_summary=f"P bands: {len(p_ids)} records",
        o_to_r_summary=f"R bands: {len(r_ids)} records",
        p_to_tseed_summary=f"Seed: {seed.seed_id if seed else 'none'}",
    )
    return record
