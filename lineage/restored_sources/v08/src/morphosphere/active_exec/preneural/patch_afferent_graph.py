"""Mainline PatchAfferentTransmissionGraph boundary for the preneural carrier layer.

This module intentionally distinguishes two related objects:

* PatchAfferentTransmissionGraph: the full, typed, provenance-bearing runtime
  graph used as the mainline preneural carrier boundary.
* stage1_physics.PatchGraph: a minimal diagnostic aggregation view used by
  current v8/v8.5 diagnostic runners.

The adapter in this file lets v8.5 continue to use the minimal PatchGraph while
making the mainline contract explicit and back-projectable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from morphosphere.active_exec.stage1_physics.cell_graph_state import CellGraphState, PatchGraph


class PatchNodeKind(str, Enum):
    """Canonical node kinds for the full preneural patch graph."""

    CELL_CENTER = "cell_center"
    MEMBRANE_PATCH = "membrane_patch"
    SYNAPSE_PATCH = "synapse_patch"
    AFFERENT_TERMINAL = "afferent_terminal"


class PatchEdgeKind(str, Enum):
    """Canonical edge kinds for the full preneural patch graph."""

    CONTACT = "contact"
    SYNAPTIC = "synaptic"
    FUNCTIONAL_COUPLING = "functional_coupling"
    SPATIAL_PROXIMITY = "spatial_proximity"
    DIAGNOSTIC_AGGREGATION = "diagnostic_aggregation"


@dataclass(frozen=True)
class PatchAnchor:
    """Spatial and provenance anchor for a patch node."""

    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    scale: float
    source_cell_ids: tuple[int, ...]
    weights_to_cells: tuple[float, ...]
    provenance_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "position": list(self.position),
            "normal": list(self.normal),
            "scale": self.scale,
            "source_cell_ids": list(self.source_cell_ids),
            "weights_to_cells": list(self.weights_to_cells),
            "provenance_hash": self.provenance_hash,
        }


@dataclass(frozen=True)
class PatchAfferentNode:
    """Typed node in the full PatchAfferentTransmissionGraph."""

    node_id: int
    node_kind: PatchNodeKind
    anchor: PatchAnchor
    V_hair_cell: float = -65.0
    calcium: float = 0.0
    release_rate: float = 0.0
    V_afferent: float = -70.0
    met_open_probability: float = 0.0
    spike_rate: float = 0.0
    regularity: float = 0.0
    timing_precision: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_kind": self.node_kind.value,
            "anchor": self.anchor.to_dict(),
            "V_hair_cell": self.V_hair_cell,
            "calcium": self.calcium,
            "release_rate": self.release_rate,
            "V_afferent": self.V_afferent,
            "met_open_probability": self.met_open_probability,
            "spike_rate": self.spike_rate,
            "regularity": self.regularity,
            "timing_precision": self.timing_precision,
        }


@dataclass(frozen=True)
class PatchAfferentEdge:
    """Typed edge in the full PatchAfferentTransmissionGraph."""

    source: int
    target: int
    edge_kind: PatchEdgeKind
    weight: float = 1.0
    delay: float = 0.0
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_kind": self.edge_kind.value,
            "weight": self.weight,
            "delay": self.delay,
            "provenance": self.provenance,
        }


@dataclass
class PatchAfferentTransmissionGraph:
    """Full preneural runtime graph.

    This is the mainline boundary.  The smaller ``PatchGraph`` remains a
    diagnostic/minimal aggregation view and should not be documented as a full
    PatchAfferentTransmissionGraph without passing through this crosswalk.
    """

    clock_n: int
    run_id: str = ""
    nodes: list[PatchAfferentNode] = field(default_factory=list)
    edges: list[PatchAfferentEdge] = field(default_factory=list)
    source_kind: str = "mainline_patch_afferent_graph"
    graph_hash: str = ""

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    @property
    def source_cell_ids(self) -> list[int]:
        cells: set[int] = set()
        for node in self.nodes:
            cells.update(node.anchor.source_cell_ids)
        return sorted(cells)

    def nodes_by_kind(self, kind: PatchNodeKind) -> list[PatchAfferentNode]:
        return [n for n in self.nodes if n.node_kind == kind]

    def adjacency_list(self, node_id: int) -> list[int]:
        neighbors: list[int] = []
        for edge in self.edges:
            if edge.source == node_id:
                neighbors.append(edge.target)
            elif edge.target == node_id:
                neighbors.append(edge.source)
        return sorted(set(neighbors))

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_n": self.clock_n,
            "run_id": self.run_id,
            "source_kind": self.source_kind,
            "graph_hash": self.graph_hash,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


def build_patch_afferent_graph_from_minimal_patch_graph(
    patch_graph: PatchGraph,
    cell_state: CellGraphState | None = None,
    *,
    run_id: str = "",
) -> PatchAfferentTransmissionGraph:
    """Promote a minimal v8/v8.5 PatchGraph into the mainline graph contract.

    The conversion is intentionally explicit.  It preserves source cell IDs,
    patch weights, v_afferent aggregates, geometry when available, and marks the
    provenance as ``diagnostic_minimal_patch_graph_crosswalk``.
    """

    positions = _positions_from_cell_state(cell_state)
    center = np.mean(positions, axis=0) if positions is not None and len(positions) else np.zeros(3)
    state_hash = _state_provenance(cell_state, patch_graph)
    nodes: list[PatchAfferentNode] = []

    for patch_id in range(patch_graph.num_patches):
        cell_ids = tuple(int(c) for c in patch_graph.source_cell_ids.get(patch_id, []))
        weights = _normalized_weights(patch_graph.patch_weights.get(patch_id, []), len(cell_ids))
        position = _weighted_position(positions, cell_ids, weights)
        normal = _normal_from_center(position, center)
        scale = _support_scale(positions, cell_ids, position)
        anchor = PatchAnchor(
            position=tuple(float(x) for x in position),
            normal=tuple(float(x) for x in normal),
            scale=float(scale),
            source_cell_ids=cell_ids,
            weights_to_cells=tuple(float(w) for w in weights),
            provenance_hash=f"{state_hash}:minimal_patch:{patch_id}",
        )
        nodes.append(
            PatchAfferentNode(
                node_id=patch_id,
                node_kind=PatchNodeKind.MEMBRANE_PATCH,
                anchor=anchor,
                V_hair_cell=_weighted_signal(cell_state.v_hair_cell if cell_state else [], cell_ids, weights, -65.0),
                calcium=_weighted_signal(cell_state.calcium_concentration if cell_state else [], cell_ids, weights, 0.0),
                release_rate=_weighted_signal(
                    cell_state.neurotransmitter_release_rate if cell_state else [], cell_ids, weights, 0.0
                ),
                V_afferent=_patch_afferent_value(patch_graph, patch_id),
                met_open_probability=_weighted_signal(
                    cell_state.met_open_probability if cell_state else [], cell_ids, weights, 0.0
                ),
            )
        )

    edges = _build_spatial_edges(nodes)
    graph = PatchAfferentTransmissionGraph(
        clock_n=int(patch_graph.clock_n),
        run_id=run_id or (cell_state.run_id if cell_state is not None else ""),
        nodes=nodes,
        edges=edges,
        source_kind="diagnostic_minimal_patch_graph_crosswalk",
    )
    graph.graph_hash = _hash_graph(graph)
    return graph


def _positions_from_cell_state(cell_state: CellGraphState | None) -> np.ndarray | None:
    if cell_state is None:
        return None
    return cell_state.get_positions_array()


def _state_provenance(cell_state: CellGraphState | None, patch_graph: PatchGraph) -> str:
    if cell_state is not None and cell_state.provenance_hash:
        return cell_state.provenance_hash
    material = f"clock={patch_graph.clock_n};patches={patch_graph.num_patches};sources={patch_graph.source_cell_ids}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _normalized_weights(weights: Sequence[float], expected_len: int) -> tuple[float, ...]:
    if expected_len <= 0:
        return tuple()
    if len(weights) != expected_len:
        return tuple([1.0 / expected_len] * expected_len)
    total = float(sum(weights))
    if abs(total) < 1e-12:
        return tuple([1.0 / expected_len] * expected_len)
    return tuple(float(w) / total for w in weights)


def _weighted_position(positions: np.ndarray | None, cell_ids: Sequence[int], weights: Sequence[float]) -> np.ndarray:
    if positions is None or not cell_ids:
        return np.zeros(3, dtype=float)
    valid: list[tuple[int, float]] = [(int(c), float(w)) for c, w in zip(cell_ids, weights) if 0 <= int(c) < len(positions)]
    if not valid:
        return np.zeros(3, dtype=float)
    total = sum(w for _, w in valid)
    if abs(total) < 1e-12:
        total = 1.0
    out = np.zeros(3, dtype=float)
    for cid, weight in valid:
        out += positions[cid] * (weight / total)
    return out


def _normal_from_center(position: np.ndarray, center: np.ndarray) -> np.ndarray:
    delta = position - center
    norm = float(np.linalg.norm(delta))
    if norm <= 1e-12:
        return np.array([0.0, 0.0, 1.0], dtype=float)
    return delta / norm


def _support_scale(positions: np.ndarray | None, cell_ids: Sequence[int], position: np.ndarray) -> float:
    if positions is None or not cell_ids:
        return 1.0
    distances = [float(np.linalg.norm(positions[int(cid)] - position)) for cid in cell_ids if 0 <= int(cid) < len(positions)]
    return max(distances) if distances else 1.0


def _weighted_signal(values: Sequence[float], cell_ids: Sequence[int], weights: Sequence[float], default: float) -> float:
    if not values or not cell_ids:
        return float(default)
    total = 0.0
    seen = 0.0
    for cid, weight in zip(cell_ids, weights):
        if 0 <= int(cid) < len(values):
            total += float(values[int(cid)]) * float(weight)
            seen += float(weight)
    return total / seen if seen > 1e-12 else float(default)


def _patch_afferent_value(patch_graph: PatchGraph, patch_id: int) -> float:
    values = patch_graph.v_afferent_aggregated
    if 0 <= patch_id < len(values):
        return float(values[patch_id])
    return -70.0


def _build_spatial_edges(nodes: Sequence[PatchAfferentNode]) -> list[PatchAfferentEdge]:
    if len(nodes) < 2:
        return []
    edges: list[PatchAfferentEdge] = []
    positions = np.array([n.anchor.position for n in nodes], dtype=float)
    for idx, node in enumerate(nodes):
        distances = np.linalg.norm(positions - positions[idx], axis=1)
        candidates = [(float(d), j) for j, d in enumerate(distances) if j != idx]
        if not candidates:
            continue
        _, nearest = min(candidates)
        src = int(min(node.node_id, nodes[nearest].node_id))
        tgt = int(max(node.node_id, nodes[nearest].node_id))
        if src == tgt:
            continue
        if any(e.source == src and e.target == tgt for e in edges):
            continue
        d = float(np.linalg.norm(positions[src] - positions[tgt]))
        weight = float(np.exp(-d))
        edges.append(
            PatchAfferentEdge(
                source=src,
                target=tgt,
                edge_kind=PatchEdgeKind.SPATIAL_PROXIMITY,
                weight=weight,
                delay=d,
                provenance="diagnostic_minimal_patch_graph_crosswalk",
            )
        )
    return edges


def _hash_graph(graph: PatchAfferentTransmissionGraph) -> str:
    material = repr(graph.to_dict()).encode("utf-8")
    return hashlib.sha256(material).hexdigest()
