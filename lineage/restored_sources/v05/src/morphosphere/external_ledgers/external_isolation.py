from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Any
from .variational_closure import VariationalLedgerClosure

@dataclass
class ExternalIsolationReport:
    schema_version: str = "v7.0.0"
    run_id: str = ""
    stage_k_id: str = ""
    window_id: str = ""
    related_T_ref: Optional[str] = None
    related_O_ref: Optional[str] = None
    related_P_refs: List[str] = field(default_factory=list)
    related_R_refs: List[str] = field(default_factory=list)
    related_origin_ref: Optional[str] = None
    external_free_energy: float = 0.0
    balance_summary: str = "Ok"
    recommended_validation_path: Optional[str] = None
    linked_ledger_refs: List[str] = field(default_factory=list)

class ExternalLedgerRunner(Protocol):
    def step(self, stage_packet: Any, observable: Any, frozen_objects: Any, transition_record: Any) -> ExternalIsolationReport:
        ...

class DefaultExternalLedgerRunner:
    def __init__(self):
        self.closure = VariationalLedgerClosure()

    def step(self, stage_packet: Any, observable: Any, frozen_objects: Any, transition_record: Any) -> ExternalIsolationReport:
        # Compute real variational free energy based on the dominant P_band
        f_ext = 0.0
        if frozen_objects and len(frozen_objects) > 0:
            f_ext = self.closure.compute_free_energy(observable, frozen_objects[0])
            
        return ExternalIsolationReport(
            external_free_energy=f_ext
        )
