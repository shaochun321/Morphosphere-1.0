from typing import Any, List, Optional, Tuple
from pydantic import BaseModel, Field

class GeometryNode(BaseModel):
    """GeometryNode: 前神经承载层的几何锚点 (V8 §7.2 compliant)"""
    node_id: int = Field(..., description="Unique node identifier")
    patch_ids: List[int] = Field(default_factory=list, description="Source patches mapped to this node")
    position: Tuple[float, float, float] = Field(..., description="3D coordinates (x, y, z)")
    surface_normal: Tuple[float, float, float] = Field(..., description="3D normal vector")
    area_weight: float = Field(default=1.0, description="Surface area weighting factor")

    # V8 §7.2 required fields
    boundary_distance: float = Field(default=0.0, description="Distance to nearest boundary")
    support_radius: float = Field(default=1.0, description="Local support radius for patch aggregation")
    neighbor_ids: List[int] = Field(default_factory=list, description="Topological neighbor node IDs")
    source_patch_ids: List[int] = Field(default_factory=list, description="Original source patch IDs for provenance")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "GeometryNode":
        return cls.model_validate(row)
