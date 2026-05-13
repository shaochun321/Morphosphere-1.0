from typing import Any
from pydantic import BaseModel, Field

class BoundaryElasticityRecord(BaseModel):
    """BoundaryElasticityRecord: 边界弹性记录"""
    boundary_id: str = Field(..., description="Unique boundary ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    elasticity_score: float = Field(..., description="Calculated elasticity score")
    elasticity_type: str = Field(default="standard", description="Type of elasticity")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "BoundaryElasticityRecord":
        return cls.model_validate(row)
