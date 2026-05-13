from typing import Any, List
from pydantic import BaseModel, Field

class OriginAnchorBundle(BaseModel):
    """OriginAnchorBundle: 多证据收束的原点锚定束 (Omega_k)"""
    origin_id: str = Field(..., description="Unique origin ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    supporting_p_ids: List[str] = Field(default_factory=list, description="P band IDs supporting this origin")
    stability_score: float = Field(default=0.0, description="Calculated stability score")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OriginAnchorBundle":
        return cls.model_validate(row)
