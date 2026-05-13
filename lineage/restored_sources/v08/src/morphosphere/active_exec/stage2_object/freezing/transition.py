import uuid
from typing import Any, List
from pydantic import BaseModel, Field
from .p_band_freezer import PrimaryBandRecord
from .r_band_freezer import ResidualBandRecord
from .origin_bundle import OriginAnchorBundle

class TSeedReplayPacket(BaseModel):
    """TSeedReplayPacket: 下一阶段输入种子包 (T_seed)"""
    seed_id: str = Field(..., description="Unique T_seed ID")
    transition_id: str = Field(..., description="Source Transition ID")
    source_p_ids: List[str] = Field(default_factory=list, description="Source P band IDs")
    allowed_drive_envelope: str = Field(default="", description="Allowed generative envelope")
    expected_region: str = Field(default="", description="Expected topological region")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "TSeedReplayPacket":
        return cls.model_validate(row)


class RecursiveTransitionRecord(BaseModel):
    """RecursiveTransitionRecord: 阶段跃迁记录"""
    transition_id: str = Field(..., description="Unique transition ID")
    from_stage_k: int = Field(..., description="From stage k")
    to_stage_kplus1: int = Field(..., description="To stage k+1")
    
    source_p_ids: List[str] = Field(default_factory=list, description="Source P band IDs")
    triggering_r_ids: List[str] = Field(default_factory=list, description="Triggering R band IDs")
    origin_id: str = Field(..., description="Origin Anchor ID")
    seed_id: str = Field(..., description="Generated T_seed ID")
    
    transition_confidence: float = Field(default=0.0, description="Confidence of transition")
    continuity_score: float = Field(default=0.0, description="Continuity/smoothness score")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RecursiveTransitionRecord":
        return cls.model_validate(row)


class TransitionBuilder:
    """TransitionBuilder: Constructs T_seed and Transition record."""
    def build_transition(self, stage_k: int, p_bands: List[PrimaryBandRecord], r_bands: List[ResidualBandRecord], origin: OriginAnchorBundle) -> tuple[RecursiveTransitionRecord, TSeedReplayPacket]:
        transition_id = f"trans_{uuid.uuid4().hex[:8]}"
        seed_id = f"seed_{uuid.uuid4().hex[:8]}"
        
        p_ids = [p.p_band_id for p in p_bands]
        r_ids = [r.r_band_id for r in r_bands]
        
        t_seed = TSeedReplayPacket(
            seed_id=seed_id,
            transition_id=transition_id,
            source_p_ids=p_ids,
            allowed_drive_envelope="standard_evolution",
            expected_region="global"
        )
        
        record = RecursiveTransitionRecord(
            transition_id=transition_id,
            from_stage_k=stage_k,
            to_stage_kplus1=stage_k + 1,
            source_p_ids=p_ids,
            triggering_r_ids=r_ids,
            origin_id=origin.origin_id,
            seed_id=seed_id,
            transition_confidence=0.95,
            continuity_score=0.9
        )
        
        return record, t_seed
