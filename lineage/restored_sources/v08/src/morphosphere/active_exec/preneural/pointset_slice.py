from typing import Any, List, Optional
from pydantic import BaseModel, Field
from .geometry import GeometryNode
from .signal_window import SignalWindow

class PreNeuralPointSetSlice(BaseModel):
    """PreNeuralPointSetSlice: 某个时间窗上可回投的 3D 拓扑点集 (V8 §1.2 compliant)

    The point-set slice is the ontological primary: all matrices, fields,
    and candidate surfaces are views of this slice, never the reverse.
    """
    slice_id: str = Field(..., description="Unique slice identifier")
    window_id: str = Field(..., description="Reference to AnalysisWindow")
    stage_k: int = Field(default=0, description="Stage index for pipeline ordering")
    
    # Structure
    geometry_node_ids: List[int] = Field(default_factory=list, description="Nodes in this slice")
    edges: List[List[int]] = Field(default_factory=list, description="Topological edges [[node_i, node_j], ...]")
    
    # V8 T1: Carried runtime objects (geometry/signal/topology/provenance)
    geometry_nodes: List[GeometryNode] = Field(default_factory=list, description="Populated GeometryNode carrier objects")
    signal_windows: List[SignalWindow] = Field(default_factory=list, description="Populated SignalWindow carrier objects")
    
    # V8.3 P1: Resolvable composite-key references (v8.1-T2)
    # Each ref is {"window_id": str, "node_id": int} for v8.3+, or str for legacy
    signal_windows_refs: List[Any] = Field(default_factory=list, description="References to SignalWindow records")
    
    # Provenance
    provenance_hash: str = Field(default="", description="SHA256 hash of source state for replay alignment")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PreNeuralPointSetSlice":
        return cls.model_validate(row)
