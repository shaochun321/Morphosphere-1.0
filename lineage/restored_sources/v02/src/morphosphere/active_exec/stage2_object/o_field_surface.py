from typing import Any, List
from pydantic import BaseModel, Field

class OFieldSurface(BaseModel):
    """OFieldSurface: 从 T_k 中组织出的候选场层"""
    field_id: str = Field(..., description="Unique field ID")
    t_surface_id: str = Field(..., description="Source T_k ID")
    
    # Optional field matrix representation
    field_matrix: List[List[float]] = Field(default_factory=list, description="State field representation")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OFieldSurface":
        return cls.model_validate(row)
