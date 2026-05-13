# Tags: [SEMANTIC_ASSETS][READ_ONLY][VERSIONED]
# Role: Historical semantic assets — term registry, field mapping, replay index.
# Must Not: Write back to active_exec. Read-only reference material.
# Producers: Extracted from v1.7.1 semantic_assets/library.py
# Consumers: semantic_readout, comparison tools, audit
"""Semantic Assets — read-only historical reference material (v5 §9.2).

Contains:
  - Term registry: canonical terms extracted from v1 SemanticLibrary
  - Field mapping: legacy_to_v5.yaml
  - Replay index: case-to-canonical mapping

ALL content is READ-ONLY. No write-back to active_exec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


# ── Term Registry (extracted from v1 SemanticTerm layer) ────────────────────

TERM_REGISTRY: list[dict[str, Any]] = [
    {
        "term": "shell0",
        "canonical_object": "stage1.surface_boundary_shell",
        "aliases": ["surface shell", "boundary shell"],
        "status": "active",
        "v5_mapping": "shell0/boundary_hypothesis.py → Shell0Determination",
    },
    {
        "term": "family surface",
        "canonical_object": "family_matrix_surface.runtime_plane",
        "aliases": ["family matrix surface", "runtime face", "completion surface"],
        "status": "active",
        "v5_mapping": "trajectory/o_surface.py → ObservableSurface (neutral replacement)",
    },
    {
        "term": "attribution packet",
        "canonical_object": "compile_signal_packet",
        "aliases": ["compile packet", "signal packet"],
        "status": "active",
        "v5_mapping": "preneural/preneural_slice.py → PreNeuralPointSetSlice",
    },
    {
        "term": "reader",
        "canonical_object": "archive.reader_reference",
        "aliases": ["summary reader", "legacy reader"],
        "status": "archive_only",
        "v5_mapping": "archive_access/v1_reader.py → V1Reader",
    },
    {
        "term": "audit",
        "canonical_object": "archive.audit_reference",
        "aliases": ["verdict", "audit artifact"],
        "status": "archive_only",
        "v5_mapping": "core/contracts.py → contract checks",
    },
    {
        "term": "origin_anchor_bundle",
        "canonical_object": "family_matrix_surface.anchor_bundle",
        "aliases": ["anchor bundle"],
        "status": "active",
        "v5_mapping": "trajectory/origin.py → OriginAnchorBundle",
    },
    {
        "term": "p/r band",
        "canonical_object": "family_matrix_surface.pr_band_projection",
        "aliases": ["pband", "rband"],
        "status": "active",
        "v5_mapping": "trajectory/band_records.py → PrimaryBandRecord / ResidualBandRecord",
    },
]


# ── Replay Index (extracted from v1 CaseAlignment layer) ───────────────────

REPLAY_INDEX: list[dict[str, Any]] = [
    {
        "case_id": "baseline",
        "legacy_label": "raw_stage1_reference",
        "canonical_case": "baseline",
        "status": "active",
        "v5_replay": "Run with zero stimulus as reference",
    },
    {
        "case_id": "translation",
        "legacy_label": "translation_demo",
        "canonical_case": "translation_family_probe",
        "status": "active",
        "v5_replay": "Run with stimulus_type='translation', compare P/R decomposition",
    },
    {
        "case_id": "rotation",
        "legacy_label": "rotation_demo",
        "canonical_case": "rotation_family_probe",
        "status": "active",
        "v5_replay": "Run with stimulus_type='rotation', compare P/R decomposition",
    },
    {
        "case_id": "boundary",
        "legacy_label": "varies by solver",
        "canonical_case": "stage1_solver",
        "status": "active",
        "v5_replay": "Compare shell0 determination across solvers",
    },
    {
        "case_id": "surface_attribute_counterfactual",
        "legacy_label": "surface_attribute",
        "canonical_case": "counterfactual.surface_attribute",
        "status": "archive_only",
        "v5_replay": "Retained as semantic replay case",
    },
]


def get_term_registry() -> list[dict[str, Any]]:
    """Get the full term registry."""
    return list(TERM_REGISTRY)


def get_replay_index() -> list[dict[str, Any]]:
    """Get the replay index."""
    return list(REPLAY_INDEX)


def get_field_mapping_path() -> Path:
    """Get path to the field mapping YAML."""
    return Path(__file__).parent / "field_mapping" / "legacy_to_v5.yaml"


def export_replay_index(path: str | Path) -> None:
    """Export the replay index to JSON."""
    Path(path).write_text(
        json.dumps(REPLAY_INDEX, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
