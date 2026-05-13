from dataclasses import dataclass, field
from typing import Optional

@dataclass
class EntropyLedgerRow:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    transport_entropy: float = 0.0
    candidate_fragment_entropy: float = 0.0
    origin_support_entropy: float = 0.0
    residual_accumulation_entropy: float = 0.0
    external_entropy_total: float = 0.0
    calculation_variant: str = "v1_minimal"
    evidence_ref: Optional[str] = None
    transport_ref: Optional[str] = None
