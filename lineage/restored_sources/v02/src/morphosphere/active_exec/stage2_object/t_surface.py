from typing import Any, List
from pydantic import BaseModel, Field

class TStagePacket(BaseModel):
    """TStagePacket: 当前阶段可处理的前语义时空点集包 (T_k)

    V8.3 P2: transport_mode enforces v8.1-T5 transport refs requirement.
    """
    t_surface_id: str = Field(..., description="Unique T-surface ID")
    stage_k: int = Field(..., description="Stage index k")

    slice_ids: List[str] = Field(default_factory=list, description="List of PreNeuralPointSetSlice IDs")
    transport_ids: List[str] = Field(default_factory=list, description="List of TransportOperator IDs")
    transport_mode: str = Field(
        default="connected",
        description="Transport mode: 'initial' (stage_k=0), 'connected', 'disconnected_initialization', 'transport_failed'"
    )

    def validate_transport_refs(self) -> List[str]:
        """V8.3 P2: Validate transport reference completeness.

        Returns list of violations.
        """
        violations = []
        if self.stage_k == 0:
            if self.transport_mode not in ("initial", "disconnected_initialization"):
                violations.append(f"stage_k=0 should have transport_mode='initial', got '{self.transport_mode}'")
        else:
            if not self.transport_ids and self.transport_mode == "connected":
                violations.append(
                    f"stage_k={self.stage_k} has transport_mode='connected' but empty transport_ids"
                )
        return violations

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "TStagePacket":
        return cls.model_validate(row)

