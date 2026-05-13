from typing import Any, Dict
from pydantic import BaseModel, Field

class SignalWindow(BaseModel):
    """SignalWindow: 节点在窗口上的纯信息状态 (V8 §7.2 compliant)"""
    window_id: str = Field(..., description="Reference to AnalysisWindow")
    node_id: int = Field(..., description="Reference to GeometryNode")
    
    # V8 §7.2 required signal fields
    V_mean: float = Field(default=0.0, description="Mean membrane potential over window")
    V_slope: float = Field(default=0.0, description="Slope of membrane potential trend")
    release_proxy: float = Field(default=0.0, description="Neurotransmitter release proxy")
    afferent_current: float = Field(default=0.0, description="Afferent synaptic current")
    spike_rate: float = Field(default=0.0, description="Spike rate (Hz)")
    spike_regularity: float = Field(default=0.0, description="CV of interspike intervals (lower = more regular)")
    timing_precision: float = Field(default=0.0, description="Phase-locking metric or timing precision")
    adaptation_state: float = Field(default=0.0, description="Adaptation variable state")

    # Legacy compatibility
    features: Dict[str, float] = Field(default_factory=dict, description="Additional extracted signal features")
    energy_level: float = Field(default=0.0, description="Signal energy")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "SignalWindow":
        return cls.model_validate(row)
