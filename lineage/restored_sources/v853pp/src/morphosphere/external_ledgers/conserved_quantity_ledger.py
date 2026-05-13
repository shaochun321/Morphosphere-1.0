from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ConservedQuantityLedgerRow:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    symmetry_id: str = ""
    quantity_name: str = ""
    ledger_value_before: float = 0.0
    ledger_value_after: float = 0.0
    source_term: float = 0.0
    dissipation_term: float = 0.0
    anomaly_term: float = 0.0
    balance_residual: float = 0.0
    evidence_ref: Optional[str] = None
    linked_object_refs: List[str] = field(default_factory=list)
