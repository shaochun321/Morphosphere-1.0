from dataclasses import dataclass
from typing import Optional

@dataclass
class NoiseBudgetLedgerRow:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    noise_budget_ext: float = 0.0
    noise_budget_measurement: float = 0.0
    noise_budget_windowing: float = 0.0
    noise_budget_transport: float = 0.0
    noise_budget_boundary: float = 0.0
    noise_budget_total: float = 0.0
    noise_source_manifest: Optional[str] = None
    budget_unit_policy: str = "ledger_unit"
