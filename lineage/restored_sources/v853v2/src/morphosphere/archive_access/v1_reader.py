# Tags: [ARCHIVE_ACCESS][LEGACY_READONLY][VERSIONED]
# Role: Read-only access to v1.7.1 (morphosphere_core) data formats.
# Must Not: Write back to active_exec or modify v1 data.
# Producers: v1 pipeline outputs (JSON, SQLite)
# Consumers: replay_alignment, semantic_assets, comparison tools
"""V1 Reader — read-only access to morphosphere_core v1.7.1 outputs.

Provides structured readers for all v1 output formats:
  - refactor_summary.json
  - manifold_trace.json
  - family_evidence.json
  - compile_signal_trace.json
  - object_core_trace.json (PBand, RBand, AnchorBundle, TSeed)
  - shell0_diagnosis.json
  - shell0_nature_assessment.json
  - semantic_library.json
  - boundary_experiment_suite.json
  - pipeline_timeseries.sqlite

ALL access is READ-ONLY. No write-back to active_exec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class V1RefactorSummary:
    """Parsed v1 refactor_summary.json."""
    project_name: str = ""
    scenario: str = ""
    stage1_frames: int = 0
    dominant_family: str = ""
    shell0_verdict: str = ""
    shell0_nature: str = ""
    shell0_nature_confidence: float = 0.0
    selected_boundary_variant: str = ""
    abstraction_budget_entered: bool = False
    semantic_ready_for_pruning: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "scenario": self.scenario,
            "stage1_frames": self.stage1_frames,
            "dominant_family": self.dominant_family,
            "shell0_verdict": self.shell0_verdict,
            "shell0_nature": self.shell0_nature,
            "selected_boundary_variant": self.selected_boundary_variant,
        }


@dataclass(frozen=True)
class V1ObjectCoreRecord:
    """Parsed v1 object_core_trace entry (PBand/RBand/AnchorBundle/TSeed)."""
    step_index: int = 0
    time: float = 0.0
    origin_anchor_bundle: dict = field(default_factory=dict)
    p_band: dict = field(default_factory=dict)
    r_band: dict = field(default_factory=dict)
    t_seed: dict = field(default_factory=dict)

    @property
    def p_family(self) -> str:
        return self.p_band.get("family", "")

    @property
    def r_family(self) -> str:
        return self.r_band.get("family", "")

    @property
    def r_reason(self) -> str:
        return self.r_band.get("reason", "")

    @property
    def t_seed_family(self) -> str:
        return self.t_seed.get("dominant_family", "")


@dataclass(frozen=True)
class V1Shell0Diagnosis:
    """Parsed v1 shell0_diagnosis.json."""
    verdict: str = ""
    energy_ratio: float = 0.0
    artifact_support_ratio: float = 0.0
    raw_data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class V1ManifoldFrame:
    """Parsed v1 manifold_trace entry."""
    time: float = 0.0
    motion_class: str = ""
    shell_boundary: list = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)


class V1Reader:
    """Read-only reader for morphosphere_core v1.7.1 pipeline outputs.

    Usage:
        reader = V1Reader("path/to/v1/output")
        summary = reader.read_summary()
        objects = reader.read_object_core_trace()
        diagnosis = reader.read_shell0_diagnosis()
    """

    def __init__(self, output_dir: str | Path):
        self.root = Path(output_dir)
        if not self.root.exists():
            raise FileNotFoundError(f"V1 output directory not found: {self.root}")

    def _load_json(self, relative_path: str) -> Any:
        """Load a JSON file from the output directory."""
        path = self.root / relative_path
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def read_summary(self) -> V1RefactorSummary | None:
        """Read refactor_summary.json."""
        data = self._load_json("refactor_summary.json")
        if data is None:
            return None
        return V1RefactorSummary(
            project_name=data.get("project_name", ""),
            scenario=data.get("scenario", ""),
            stage1_frames=data.get("stage1_frames", 0),
            dominant_family=data.get("dominant_family", ""),
            shell0_verdict=data.get("shell0_verdict", ""),
            shell0_nature=data.get("shell0_nature", ""),
            shell0_nature_confidence=data.get("shell0_nature_confidence", 0.0),
            selected_boundary_variant=data.get("selected_boundary_variant", ""),
            abstraction_budget_entered=data.get("abstraction_budget_entered", False),
            semantic_ready_for_pruning=data.get("semantic_ready_for_pruning", False),
        )

    def read_object_core_trace(self) -> list[V1ObjectCoreRecord]:
        """Read object_core_trace.json from neural_mesh."""
        data = self._load_json("neural_mesh/object_core_trace.json")
        if data is None:
            return []
        return [
            V1ObjectCoreRecord(
                step_index=entry.get("step_index", 0),
                time=entry.get("time", 0.0),
                origin_anchor_bundle=entry.get("origin_anchor_bundle", {}),
                p_band=entry.get("p_band", {}),
                r_band=entry.get("r_band", {}),
                t_seed=entry.get("t_seed", {}),
            )
            for entry in data
        ]

    def read_shell0_diagnosis(self) -> V1Shell0Diagnosis | None:
        """Read shell0_diagnosis.json from contracts."""
        data = self._load_json("contracts/shell0_diagnosis.json")
        if data is None:
            return None
        return V1Shell0Diagnosis(
            verdict=data.get("verdict", ""),
            energy_ratio=data.get("energy_ratio", 0.0),
            artifact_support_ratio=data.get("artifact_support_ratio", 0.0),
            raw_data=data,
        )

    def read_manifold_trace(self) -> list[V1ManifoldFrame]:
        """Read manifold_trace.json from cell_sphere."""
        data = self._load_json("cell_sphere/manifold_trace.json")
        if data is None:
            return []
        return [
            V1ManifoldFrame(
                time=entry.get("time", 0.0),
                motion_class=entry.get("motion_class", ""),
                shell_boundary=entry.get("shell_boundary", []),
                raw_data=entry,
            )
            for entry in data
        ]

    def read_semantic_library(self) -> dict | None:
        """Read semantic_library.json."""
        return self._load_json("semantic_assets/semantic_library.json")

    def read_semantic_replay_alignment(self) -> dict | None:
        """Read semantic_replay_alignment.json."""
        return self._load_json("semantic_assets/semantic_replay_alignment.json")

    def read_family_evidence(self) -> list[dict]:
        """Read family_evidence.json from family_matrix_surface."""
        data = self._load_json("family_matrix_surface/family_evidence.json")
        return data if isinstance(data, list) else []

    def read_boundary_experiment_suite(self) -> dict | None:
        """Read boundary_experiment_suite.json."""
        return self._load_json("contracts/boundary_experiment_suite.json")

    def list_available_outputs(self) -> dict[str, bool]:
        """Check which v1 output files exist."""
        paths = {
            "refactor_summary": "refactor_summary.json",
            "manifold_trace": "cell_sphere/manifold_trace.json",
            "shell0_diagnosis": "contracts/shell0_diagnosis.json",
            "shell0_nature": "contracts/shell0_nature_assessment.json",
            "object_core_trace": "neural_mesh/object_core_trace.json",
            "compile_signal_trace": "neural_mesh/compile_signal_trace.json",
            "family_evidence": "family_matrix_surface/family_evidence.json",
            "semantic_library": "semantic_assets/semantic_library.json",
            "semantic_replay": "semantic_assets/semantic_replay_alignment.json",
            "boundary_experiments": "contracts/boundary_experiment_suite.json",
            "boundary_solver": "contracts/stage1_boundary_solver_selection.json",
            "timeseries_db": "storage/pipeline_timeseries.sqlite",
        }
        return {name: (self.root / path).exists() for name, path in paths.items()}
