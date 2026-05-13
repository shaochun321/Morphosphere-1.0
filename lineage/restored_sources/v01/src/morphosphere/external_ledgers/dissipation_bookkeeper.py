from dataclasses import dataclass
from typing import Optional

@dataclass
class DissipationLedgerRow:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    coarse_graining_dissipation: float = 0.0
    boundary_dissipation: float = 0.0
    numerical_dissipation: float = 0.0
    dissipation_total: float = 0.0
    evidence_ref: Optional[str] = None
    dissipation_variant: str = "v1_minimal"
