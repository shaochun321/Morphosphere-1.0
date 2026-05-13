from typing import Any, List, Optional
from pydantic import BaseModel, Field

class FamilyRecursiveSurfaceIndex(BaseModel):
    """FamilyRecursiveSurfaceIndex: 统一索引 origin / P/R / relation / transition / replay hooks

    V8-T4 additions:
      - maturity_flag: candidate → frozen → matured
      - suspension_status: ACTIVE / SUSPENDED_PRESENT / SUSPENDED_NUMERICAL_CLOSURE
      - aggregation_role: canonical role in the index hierarchy
      - origin_anchor_id / t_seed_id references
    """
    surface_id: str = Field(..., description="Unique Surface Index ID")
    clock_n: int = Field(..., description="Clock tick index")

    transition_ids: List[str] = Field(default_factory=list, description="Associated Transition IDs")
    shell0_verdict: str = Field(default="unknown", description="Shell0 Boundary verdict")

    # V8-T4: Maturity and suspension tracking
    maturity_flag: str = Field(
        default="candidate",
        description="Maturity state: 'candidate' | 'frozen' | 'matured'"
    )
    suspension_status: str = Field(
        default="ACTIVE",
        description="Suspension state: 'ACTIVE' | 'SUSPENDED_PRESENT' | 'SUSPENDED_NUMERICAL_CLOSURE'"
    )
    aggregation_role: str = Field(
        default="index_root",
        description="Canonical index role: 'index_root' | 'transition_hub' | 'boundary_fence'"
    )

    # V8-T4: Origin and seed references
    origin_anchor_id: Optional[str] = Field(default=None, description="Reference to Omega_k origin anchor bundle")
    t_seed_id: Optional[str] = Field(default=None, description="Reference to T_seed replay packet")

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "FamilyRecursiveSurfaceIndex":
        return cls.model_validate(row)
