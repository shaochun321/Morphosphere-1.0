"""RunManifest: run identity, calibration, and count semantics.

Mainline convergence keeps ``cell_count`` for backward compatibility but makes
``physical_cell_count`` and ``spacetime_cell_count`` explicit.  This avoids the
common V8.5 diagnostic ambiguity where a spacetime/runtime carrier row is
mistaken for a physical stage-1 cell.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class RunManifest(BaseModel):
    """Immutable identity record for a pipeline run.

    ``cell_count`` is deprecated/ambiguous and retained only for compatibility
    with pre-convergence migrations and diagnostics.  New code should populate
    ``physical_cell_count`` and ``spacetime_cell_count``.
    """

    run_id: str = Field(..., description="Unique run identifier")
    rules_version: str = Field(default="v8.3", description="Morphosphere rules version")
    schema_version: str = Field(default="v8.3", description="Database schema version")
    calibration_profile: str = Field(
        default="default_v83",
        description="Calibration profile for threshold, ledger, and measure comparability",
    )
    execution_mode: str = Field(
        default="diagnostic",
        description="Run mode: diagnostic / diagnostic_full / scaffold / candidate_validating / scientific",
    )
    input_source: Optional[str] = Field(default=None, description="Input data source description")
    cell_count: int = Field(
        default=0,
        description="Deprecated compatibility count; prefer physical_cell_count/spacetime_cell_count",
    )
    physical_cell_count: int = Field(
        default=0,
        description="Number of physical stage-1 cells in PhysicalCellGraphState",
    )
    window_count: int = Field(default=0, description="Number of analysis windows")
    spacetime_cell_count: int = Field(
        default=0,
        description="Number of derived diagnostic spacetime/runtime carrier rows",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 creation timestamp",
    )
    notes: Optional[str] = Field(default=None, description="Free-text notes")
    extra_json: str = Field(
        default="{}",
        description="Additive JSON metadata for manifest semantics and crosswalk references",
    )

    def to_row(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "RunManifest":
        return cls.model_validate(row)

    @staticmethod
    def generate_run_id(prefix: str = "run") -> str:
        """Generate a unique run ID."""
        return f"{prefix}_{uuid.uuid4().hex[:8]}"


__all__ = ["RunManifest"]
