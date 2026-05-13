from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AnomalyLedgerRow:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    anomaly_type: str = "unexplained_growth"
    anomaly_score: float = 0.0
    possible_sources: List[str] = field(default_factory=list)
    linked_object_refs: List[str] = field(default_factory=list)
    evidence_ref: Optional[str] = None
