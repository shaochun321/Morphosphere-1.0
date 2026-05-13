from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np


class CellGraphState(BaseModel):
    """CellGraphState: 时钟 n 下的物理—前神经联合真值状态

    V8 P1 fix: 统一 Pydantic model 与 V2 dataclass 的字段覆盖.
    Pydantic model 现在包含 positions, velocities, radii 等几何字段,
    与 v2_dataclass.CellGraphState 保持一致.
    """
    model_config = {"arbitrary_types_allowed": True}

    clock_n: int = Field(..., description="Canonical time index")
    run_id: str = Field(..., description="Run identifier")
    num_cells: int = Field(..., description="Number of cells")

    # [GEO] Geometric state — aligned with V2 dataclass
    positions: Any = Field(default=None, description="Cell positions (N x 3 numpy array or list)")
    velocities: Any = Field(default=None, description="Cell velocities (N x 3 numpy array or list)")
    radii: Any = Field(default=None, description="Cell radii (N numpy array or list)")

    # [TOPO] Topology flags
    active_flags: Any = Field(default=None, description="Active cell flags (N bool array or list)")

    # 5-layer electrophysiology
    v_hair_cell: List[float] = Field(default_factory=list, description="Hair cell membrane potential")
    calcium_concentration: List[float] = Field(default_factory=list, description="Intracellular Ca2+ concentration")
    v_afferent: List[float] = Field(default_factory=list, description="Afferent ending potential")
    met_open_probability: List[float] = Field(default_factory=list, description="MET channel open probability")
    neurotransmitter_release_rate: List[float] = Field(default_factory=list, description="Release rate")

    provenance_hash: str = Field(default="", description="State provenance hash")

    def get_positions_array(self) -> Optional[np.ndarray]:
        """Return positions as numpy array, or None if not set."""
        if self.positions is None:
            return None
        if isinstance(self.positions, np.ndarray):
            return self.positions
        return np.array(self.positions)

    def to_row(self) -> dict[str, Any]:
        d = self.model_dump()
        # Convert numpy arrays to lists for JSON serialization
        for k in ('positions', 'velocities', 'radii', 'active_flags'):
            v = d.get(k)
            if isinstance(v, np.ndarray):
                d[k] = v.tolist()
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CellGraphState":
        return cls.model_validate(row)


class PatchGraph(BaseModel):
    """PatchGraph: 由 cell-level 状态聚合成的 mechanotransduction patch 图"""
    clock_n: int = Field(..., description="Canonical time index")
    num_patches: int = Field(..., description="Number of aggregated patches")

    source_cell_ids: Dict[int, List[int]] = Field(default_factory=dict, description="Mapping from patch_id to cell_ids")
    patch_weights: Dict[int, List[float]] = Field(default_factory=dict, description="Weights of cells in patch")

    # Aggregated states
    v_afferent_aggregated: List[float] = Field(default_factory=list, description="Aggregated afferent potential")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "PatchGraph":
        return cls.model_validate(row)
