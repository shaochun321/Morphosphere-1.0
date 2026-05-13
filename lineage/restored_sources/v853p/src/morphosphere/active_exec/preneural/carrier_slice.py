"""Unified preneural carrier-slice boundary.

The mainline architecture treats preneural slices as back-projectable carrier
objects.  Current v8/v8.5 code uses ``PreNeuralPointSetSlice`` while legacy v2
used ``PreNeuralSlice``.  This module provides the stable crosswalk that names
both as views of a single carrier boundary without merging their implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal, Mapping, Sequence

from .pointset_slice import PreNeuralPointSetSlice

CarrierSliceKind = Literal["pointset_slice", "legacy_preneural_slice", "diagnostic_empty_slice"]


@dataclass(frozen=True)
class CarrierSignalRef:
    """Resolvable signal-window reference for a carrier node."""

    window_id: str
    node_id: int

    def to_dict(self) -> dict[str, Any]:
        return {"window_id": self.window_id, "node_id": self.node_id}


@dataclass
class PreNeuralCarrierSlice:
    """Canonical, implementation-neutral preneural carrier slice."""

    slice_id: str
    window_id: str
    stage_k: int = 0
    kind: CarrierSliceKind = "pointset_slice"
    geometry_node_ids: list[int] = field(default_factory=list)
    edges: list[list[int]] = field(default_factory=list)
    source_patch_refs: dict[int, list[int]] = field(default_factory=dict)
    source_cell_refs: dict[int, list[int]] = field(default_factory=dict)
    signal_refs: list[CarrierSignalRef] = field(default_factory=list)
    provenance_hash: str = ""
    source_note: str = ""

    @property
    def num_geometry_nodes(self) -> int:
        return len(self.geometry_node_ids)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        return {
            "slice_id": self.slice_id,
            "window_id": self.window_id,
            "stage_k": self.stage_k,
            "kind": self.kind,
            "geometry_node_ids": list(self.geometry_node_ids),
            "edges": [list(e) for e in self.edges],
            "source_patch_refs": {str(k): list(v) for k, v in self.source_patch_refs.items()},
            "source_cell_refs": {str(k): list(v) for k, v in self.source_cell_refs.items()},
            "signal_refs": [r.to_dict() for r in self.signal_refs],
            "provenance_hash": self.provenance_hash,
            "source_note": self.source_note,
        }


def carrier_from_pointset_slice(
    pointset: PreNeuralPointSetSlice,
    *,
    patch_to_cells: Mapping[int, Sequence[int]] | None = None,
) -> PreNeuralCarrierSlice:
    """Build the canonical carrier view from the v8/v8.5 point-set slice."""

    source_patch_refs: dict[int, list[int]] = {}
    source_cell_refs: dict[int, list[int]] = {}
    for geometry_node in pointset.geometry_nodes:
        patch_ids = _as_int_list(geometry_node.source_patch_ids or geometry_node.patch_ids)
        source_patch_refs[int(geometry_node.node_id)] = patch_ids
        source_cell_refs[int(geometry_node.node_id)] = _cells_for_patches(patch_ids, patch_to_cells)

    signal_refs = [_normalize_signal_ref(ref, pointset.window_id) for ref in pointset.signal_windows_refs]
    if not signal_refs and pointset.signal_windows:
        signal_refs = [CarrierSignalRef(window_id=s.window_id, node_id=int(s.node_id)) for s in pointset.signal_windows]

    return PreNeuralCarrierSlice(
        slice_id=pointset.slice_id,
        window_id=pointset.window_id,
        stage_k=int(pointset.stage_k),
        kind="pointset_slice",
        geometry_node_ids=[int(x) for x in pointset.geometry_node_ids],
        edges=[_as_int_list(edge) for edge in pointset.edges],
        source_patch_refs=source_patch_refs,
        source_cell_refs=source_cell_refs,
        signal_refs=signal_refs,
        provenance_hash=pointset.provenance_hash,
        source_note="PreNeuralPointSetSlice is the v8/v8.5 implementation of the mainline carrier slice.",
    )


def carrier_from_legacy_slice_like(legacy_slice: Any) -> PreNeuralCarrierSlice:
    """Build the canonical carrier view from a legacy v2 PreNeuralSlice-like object.

    This adapter uses duck typing to avoid importing the sibling legacy package,
    because both projects use the same import package name ``morphosphere``.
    """

    points = list(getattr(legacy_slice, "points", []) or [])
    geometry_node_ids: list[int] = []
    source_patch_refs: dict[int, list[int]] = {}
    for idx, point in enumerate(points):
        point_id = int(getattr(point, "point_id", idx))
        geometry_node_ids.append(point_id)
        source_patch_refs[point_id] = _as_int_list(getattr(point, "source_patch_ids", []))

    return PreNeuralCarrierSlice(
        slice_id=str(getattr(legacy_slice, "slice_hash", "") or getattr(legacy_slice, "window_id", "legacy_slice")),
        window_id=str(getattr(legacy_slice, "window_id", "legacy_window")),
        stage_k=int(getattr(legacy_slice, "clock_start", 0)),
        kind="legacy_preneural_slice",
        geometry_node_ids=geometry_node_ids,
        edges=[],
        source_patch_refs=source_patch_refs,
        source_cell_refs={},
        signal_refs=[],
        provenance_hash=str(getattr(legacy_slice, "slice_hash", "")),
        source_note="Legacy v2 PreNeuralSlice-like object converted by duck-typed adapter.",
    )


def empty_diagnostic_carrier_slice(window_id: str, *, stage_k: int = 0) -> PreNeuralCarrierSlice:
    return PreNeuralCarrierSlice(
        slice_id=f"empty_{window_id}",
        window_id=window_id,
        stage_k=stage_k,
        kind="diagnostic_empty_slice",
        source_note="Diagnostic empty carrier slice; should not be treated as physical source-of-truth.",
    )


def _normalize_signal_ref(ref: Any, default_window_id: str) -> CarrierSignalRef:
    if isinstance(ref, Mapping):
        return CarrierSignalRef(window_id=str(ref.get("window_id", default_window_id)), node_id=int(ref.get("node_id", 0)))
    if isinstance(ref, str):
        # Legacy refs were sometimes opaque strings; keep a deterministic node id fallback.
        return CarrierSignalRef(window_id=default_window_id, node_id=0)
    return CarrierSignalRef(window_id=default_window_id, node_id=int(getattr(ref, "node_id", 0)))


def _cells_for_patches(patch_ids: Sequence[int], patch_to_cells: Mapping[int, Sequence[int]] | None) -> list[int]:
    if patch_to_cells is None:
        return []
    cells: set[int] = set()
    for patch_id in patch_ids:
        cells.update(int(c) for c in patch_to_cells.get(int(patch_id), []))
    return sorted(cells)


def _as_int_list(values: Iterable[Any]) -> list[int]:
    return [int(v) for v in values]
