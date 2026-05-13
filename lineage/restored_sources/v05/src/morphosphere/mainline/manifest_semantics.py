"""Canonical manifest count semantics for mainline convergence.

This module separates physical cells from diagnostic/runtime spacetime cells.
``cell_count`` is kept only for backward compatibility; new code should use
``physical_cell_count`` and ``spacetime_cell_count`` explicitly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ManifestCountSemantics:
    """Explicit run count semantics used by manifests and acceptance reports."""

    physical_cell_count: int
    window_count: int
    spacetime_cell_count: int
    legacy_cell_count: int | None = None

    @classmethod
    def from_physical_and_windows(
        cls,
        *,
        physical_cell_count: int,
        window_count: int,
        legacy_cell_count: int | None = None,
    ) -> "ManifestCountSemantics":
        physical = int(physical_cell_count)
        windows = int(window_count)
        return cls(
            physical_cell_count=physical,
            window_count=windows,
            spacetime_cell_count=physical * windows,
            legacy_cell_count=legacy_cell_count,
        )

    @classmethod
    def from_runtime_rows(
        cls,
        *,
        physical_cell_count: int,
        window_count: int,
        spacetime_cell_rows: int,
        legacy_cell_count: int | None = None,
    ) -> "ManifestCountSemantics":
        return cls(
            physical_cell_count=int(physical_cell_count),
            window_count=int(window_count),
            spacetime_cell_count=int(spacetime_cell_rows),
            legacy_cell_count=legacy_cell_count,
        )

    def to_extra_dict(self) -> dict[str, Any]:
        return {
            "count_semantics": {
                "physical_cell_count": self.physical_cell_count,
                "window_count": self.window_count,
                "spacetime_cell_count": self.spacetime_cell_count,
                "legacy_cell_count": self.legacy_cell_count,
                "legacy_cell_count_status": "deprecated_ambiguous",
                "physical_cell_definition": "stage1 PhysicalCellGraphState source-of-truth cell",
                "spacetime_cell_definition": "diagnostic runtime carrier row, usually physical_cell x window",
            }
        }

    def to_extra_json(self) -> str:
        return json.dumps(self.to_extra_dict(), sort_keys=True)


def merge_extra_json(existing: str | None, update: Mapping[str, Any]) -> str:
    """Merge a small dictionary into a manifest extra_json payload."""
    try:
        payload = json.loads(existing) if existing else {}
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}
    payload.update(dict(update))
    return json.dumps(payload, sort_keys=True)


__all__ = ["ManifestCountSemantics", "merge_extra_json"]
