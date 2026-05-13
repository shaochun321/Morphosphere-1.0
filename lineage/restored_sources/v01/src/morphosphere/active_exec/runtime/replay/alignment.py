import uuid
from typing import Any
from pydantic import BaseModel, Field

class ReplayAlignmentRecord(BaseModel):
    """ReplayAlignmentRecord: 验证新老架构执行一致性的审计记录"""
    alignment_id: str = Field(..., description="Unique Alignment ID")
    run_id: str = Field(..., description="Run session ID")
    v6_surface_id: str = Field(..., description="V6 ObservableSurface or FamilySurface ID")
    legacy_record_id: str = Field(..., description="ID from old trace")
    
    alignment_score: float = Field(default=0.0, description="1.0 means exact match")
    divergence_reason: str = Field(default="", description="If < 1.0, why did it diverge?")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ReplayAlignmentRecord":
        return cls.model_validate(row)

class ReplayValidator:
    def validate_alignment(self, run_id: str, v6_surface_id: str, legacy_record_id: str, score: float) -> ReplayAlignmentRecord:
        """
        Records the alignment verification result.
        """
        return ReplayAlignmentRecord(
            alignment_id=f"align_{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            v6_surface_id=v6_surface_id,
            legacy_record_id=legacy_record_id,
            alignment_score=score,
            divergence_reason="None" if score == 1.0 else "Numerical drift"
        )
