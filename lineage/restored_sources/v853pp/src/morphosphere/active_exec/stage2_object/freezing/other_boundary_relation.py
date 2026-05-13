from typing import Any
from pydantic import BaseModel, Field

class OtherBoundaryRelationRecord(BaseModel):
    """OtherBoundaryRelationRecord: 其他边界分离记录"""
    relation_id: str = Field(..., description="Unique relation ID")
    o_surface_id: str = Field(..., description="Source O_k ID")
    separation_distance: float = Field(..., description="Calculated separation distance")
    relation_type: str = Field(default="unknown", description="Type of boundary relation")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OtherBoundaryRelationRecord":
        return cls.model_validate(row)
