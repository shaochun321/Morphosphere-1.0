from typing import Any, List
from pydantic import BaseModel, Field

class OccupancyState(BaseModel):
    """OccupancyState: 占据态分布"""
    occupancy_id: str = Field(..., description="Unique occupancy state ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    occupancy_distribution: List[float] = Field(default_factory=list, description="Distribution of occupancy")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OccupancyState":
        return cls.model_validate(row)
