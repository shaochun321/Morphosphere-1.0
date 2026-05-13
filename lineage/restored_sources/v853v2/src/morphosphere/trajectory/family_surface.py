# Tags: [CORE_RUNTIME][TRAJECTORY][VERSIONED]
# Role: Unified surface combining latent objects, transition records, and evidence (v5 P09).
# Must Not: Import semantic_readout or produce semantic labels directly.
# Producers: pipeline, decomposition
# Consumers: export, replay_alignment

from dataclasses import dataclass, field
from typing import Any
from .band_records import PrimaryBandRecord, ResidualBandRecord
from .origin import RecursiveTransitionRecord

@dataclass(frozen=True)
class FamilyEvidenceRow:
    """A single row of evidence for the FamilyRecursiveSurface."""
    clock_n: int
    time: float
    transition_record: RecursiveTransitionRecord
    shell0_diagnosis: dict[str, Any] = field(default_factory=dict)
    boundary_report: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_n": self.clock_n,
            "time": self.time,
            "transition": self.transition_record.to_dict(),
            "shell0_diagnosis": self.shell0_diagnosis,
            "boundary_report": self.boundary_report,
        }

class FamilyRecursiveSurface:
    """
    Unified matrix surface storing the history of all latent objects and evidence.
    This acts as the final runtime state plane for the trajectory.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.evidence: list[FamilyEvidenceRow] = []
        
    def append_evidence(self, row: FamilyEvidenceRow) -> None:
        """Append a new evidence row to the surface."""
        self.evidence.append(row)
        
    def to_manifest(self) -> list[dict[str, Any]]:
        """Export the surface history as a manifest list."""
        return [row.to_dict() for row in self.evidence]
