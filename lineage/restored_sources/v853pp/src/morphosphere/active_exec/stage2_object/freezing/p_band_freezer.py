import uuid
from typing import Any, List
from pydantic import BaseModel, Field
from .thresholds import THETA_P

class PrimaryBandRecord(BaseModel):
    """PrimaryBandRecord: 确认核心带 (P_k)"""
    p_band_id: str = Field(..., description="Unique P band ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    core_margin_type: str = Field(..., description="Margin type")
    member_node_ids: List[int] = Field(default_factory=list, description="Node indices in this band")
    
    coherence_score: float = Field(default=0.0, description="Coherence/Energy score")
    replay_support: float = Field(default=0.0, description="Support from replay/provenance")
    origin_anchor_id: str = Field(default="", description="Origin anchor reference")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PrimaryBandRecord":
        return cls.model_validate(row)


class PBandFreezer:
    def freeze(self, o_surface_id: str, candidate_score: float, nodes: List[int]) -> PrimaryBandRecord | None:
        """Freeze a primary band if it meets the criteria."""
        if candidate_score > THETA_P:
            return PrimaryBandRecord(
                p_band_id=f"p_band_{uuid.uuid4().hex[:8]}",
                o_surface_id=o_surface_id,
                core_margin_type="stable",
                member_node_ids=nodes,
                coherence_score=candidate_score,
                replay_support=1.0
            )
        return None
