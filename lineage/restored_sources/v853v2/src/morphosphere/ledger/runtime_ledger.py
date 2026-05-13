# Tags: [LEDGER_ONLY][RECORD_ONLY][VERSIONED]
# Role: Record-only bookkeeping. NEVER drives Stage-1 ontology.
# Must Not: Write back to CellGraphState or dynamics layers.
# Producers: pipeline
# Consumers: semantic_readout (read-only), export, replay
"""Runtime Ledger — record-only bookkeeping (masterplan §9).

The ledger records cell/slice/trajectory indices, latent support,
transition fields, shell0 criteria, replay alignment results, and
external labels. It does NOT drive Stage-1 ontology.

Masterplan §9.1: 账本只记录，不驱动 Stage-1 本体。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import json
import hashlib

import numpy as np

from morphosphere.core.types import Float64Array


@dataclass
class LedgerEntry:
    """A single entry in the runtime ledger.

    Each entry records one snapshot of the system state with
    full provenance for replay alignment.
    """
    step_index: int
    time: float
    clock_n: int = 0

    # Source references (indices, not copies)
    state_hash: str = ""
    slice_hash: str = ""
    trajectory_hash: str = ""

    # Decomposition summary
    coherence_score: float = 0.0
    sparsity_score: float = 0.0
    p_energy_fraction: float = 0.0
    r_energy_fraction: float = 0.0

    # Shell0 boundary hypothesis status (masterplan §10)
    shell0_status: str = "untested"  # untested / real / construction_issue / indeterminate

    # Replay alignment
    replay_aligned: bool = False
    replay_delta: float = 0.0

    # External labels (post-hoc only, never feed back)
    external_labels: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_index": self.step_index,
            "time": self.time,
            "clock_n": self.clock_n,
            "state_hash": self.state_hash,
            "slice_hash": self.slice_hash,
            "trajectory_hash": self.trajectory_hash,
            "coherence_score": self.coherence_score,
            "sparsity_score": self.sparsity_score,
            "p_energy_fraction": self.p_energy_fraction,
            "r_energy_fraction": self.r_energy_fraction,
            "shell0_status": self.shell0_status,
            "replay_aligned": self.replay_aligned,
            "replay_delta": self.replay_delta,
            "external_labels": dict(self.external_labels),
        }


class RuntimeLedger:
    """Runtime bookkeeping ledger (masterplan §9).

    Records state/slice/trajectory provenance and decomposition metrics.
    Read-write during simulation, read-only for downstream consumers.

    CRITICAL: The ledger only records. It NEVER drives Stage-1 ontology
    or feeds back into the active runtime path.
    """

    def __init__(self, run_id: str = "default"):
        self.run_id = run_id
        self._entries: list[LedgerEntry] = []
        self._metadata: dict[str, Any] = {
            "run_id": run_id,
            "version": "2.0.0a1",
            "ledger_type": "runtime",
        }

    @property
    def num_entries(self) -> int:
        return len(self._entries)

    @property
    def entries(self) -> list[LedgerEntry]:
        return list(self._entries)

    def append(self, entry: LedgerEntry) -> None:
        """Add a new ledger entry."""
        self._entries.append(entry)

    def latest(self) -> LedgerEntry | None:
        """Get the most recent entry."""
        return self._entries[-1] if self._entries else None

    def entries_in_window(self, t_start: float, t_end: float) -> list[LedgerEntry]:
        """Get all entries within a time window."""
        return [e for e in self._entries if t_start <= e.time <= t_end]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metadata": dict(self._metadata),
            "num_entries": self.num_entries,
            "entries": [e.to_dict() for e in self._entries],
        }

    def export(self, path: Path) -> None:
        """Export ledger to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def summary(self) -> dict[str, Any]:
        """Compute summary statistics over all entries."""
        if not self._entries:
            return {"num_entries": 0}

        coherences = [e.coherence_score for e in self._entries]
        return {
            "num_entries": self.num_entries,
            "time_range": [self._entries[0].time, self._entries[-1].time],
            "mean_coherence": float(np.mean(coherences)),
            "std_coherence": float(np.std(coherences)),
            "shell0_verdicts": _count_verdicts(self._entries),
        }


def _count_verdicts(entries: list[LedgerEntry]) -> dict[str, int]:
    """Count shell0 verdict distribution."""
    counts: dict[str, int] = {}
    for e in entries:
        counts[e.shell0_status] = counts.get(e.shell0_status, 0) + 1
    return counts
