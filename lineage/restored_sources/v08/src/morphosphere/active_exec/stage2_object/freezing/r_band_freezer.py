import uuid
from typing import Any, Dict
from pydantic import BaseModel, Field
from .thresholds import THETA_R

class ResidualBandRecord(BaseModel):
    """ResidualBandRecord: 残差—边界—路由带 (R_k)"""
    r_band_id: str = Field(..., description="Unique R band ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    margin_outer_type: str = Field(..., description="Outer margin type")
    residual_reason: str = Field(..., description="Reason for residual (competition, conflict)")
    
    routing_target: str = Field(default="", description="Routing target")
    upgrade_conditions: Dict[str, float] = Field(default_factory=dict, description="Conditions to upgrade to P band")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ResidualBandRecord":
        return cls.model_validate(row)


class RBandFreezer:
    def freeze(self, o_surface_id: str, candidate_score: float) -> ResidualBandRecord | None:
        """Freeze a residual band if it meets the criteria."""
        if candidate_score > THETA_R:
            return ResidualBandRecord(
                r_band_id=f"r_band_{uuid.uuid4().hex[:8]}",
                o_surface_id=o_surface_id,
                margin_outer_type="unstable",
                residual_reason="competition",
                routing_target="none",
                upgrade_conditions={"theta_r_required": 0.8}
            )
        return None
