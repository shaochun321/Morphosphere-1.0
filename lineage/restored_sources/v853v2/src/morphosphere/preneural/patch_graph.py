"""PatchAfferentTransmissionGraph — runtime graph object (masterplan §7.1).

This is the runtime organization of the preneural layer. It connects
cell_center / membrane_patch / synapse_patch / afferent_terminal nodes
with contact / synaptic / functional_coupling / spatial_proximity edges.

Together with PreNeuralSlice, they form the two views of the same
preneural carrier layer (masterplan §7 "两层同体" principle).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib

import numpy as np

from morphosphere.core.cell_graph_state import CellGraphState
from morphosphere.core.types import (
    Float64Array,
    Int64Array,
    NodeType,
    EdgeType,
    SpatialAnchor,
)


@dataclass
class PatchNode:
    """A node in the PatchAfferentTransmissionGraph.

    Masterplan §7.1 node attributes:
        xyz, normal/scale, source_patch_ids, weights_to_cells,
        adjacency list, current continuous state
    """
    node_id: int
    node_type: NodeType
    anchor: SpatialAnchor

    # Window state (masterplan §7.1)
    rate: float = 0.0
    regularity: float = 0.0
    timing_precision: float = 0.0
    latency: float = 0.0
    burstiness: float = 0.0

    # Continuous state from CellGraphState
    V_hair_cell: float = -65.0
    calcium: float = 0.0
    release_rate: float = 0.0
    V_afferent: float = -70.0
    met_open_prob: float = 0.05

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.name,
            "position": self.anchor.position.tolist(),
            "normal": self.anchor.normal.tolist(),
            "scale": self.anchor.scale,
            "source_cell_ids": self.anchor.source_cell_ids,
            "weights_to_cells": self.anchor.weights_to_cells.tolist(),
            "provenance_hash": self.anchor.provenance_hash,
            "rate": self.rate,
            "regularity": self.regularity,
            "timing_precision": self.timing_precision,
            "latency": self.latency,
            "burstiness": self.burstiness,
            "V_hair_cell": self.V_hair_cell,
            "calcium": self.calcium,
            "release_rate": self.release_rate,
            "V_afferent": self.V_afferent,
            "met_open_prob": self.met_open_prob,
        }


@dataclass
class PatchEdge:
    """An edge in the PatchAfferentTransmissionGraph."""
    source: int
    target: int
    edge_type: EdgeType
    weight: float = 1.0
    delay: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "edge_type": self.edge_type.name,
            "weight": self.weight,
            "delay": self.delay,
        }


@dataclass
class PatchAfferentTransmissionGraph:
    """Runtime graph object for the preneural carrier layer.

    Masterplan §7.1:
        Node types: cell_center / membrane_patch / synapse_patch / afferent_terminal
        Edge types: contact / synaptic / functional_coupling / spatial_proximity
    """
    nodes: list[PatchNode] = field(default_factory=list)
    edges: list[PatchEdge] = field(default_factory=list)
    time: float = 0.0

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def node_by_type(self, ntype: NodeType) -> list[PatchNode]:
        return [n for n in self.nodes if n.node_type == ntype]

    def adjacency_list(self, node_id: int) -> list[int]:
        """Get all neighbors of a node."""
        neighbors: list[int] = []
        for e in self.edges:
            if e.source == node_id:
                neighbors.append(e.target)
            elif e.target == node_id:
                neighbors.append(e.source)
        return neighbors

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


def build_patch_graph_from_state(
    state: CellGraphState,
    afferent_stats: dict[str, Float64Array] | None = None,
) -> PatchAfferentTransmissionGraph:
    """Build a PatchAfferentTransmissionGraph from CellGraphState.

    This is the first-version patch-based vestibular-like front end
    (masterplan §5.2). Each cell becomes a node. In future versions,
    cells can be aggregated into membrane patches.

    Every node carries provenance back to the originating cell(s),
    satisfying the "可回投到 cell/patch 来源的 provenance" requirement.
    """
    graph = PatchAfferentTransmissionGraph(time=state.time)
    n = state.num_cells

    # Compute cell-level spatial info
    center = np.mean(state.positions, axis=0)
    relative = state.positions - center
    radius = np.linalg.norm(relative, axis=1)
    safe_r = np.maximum(radius, 1e-12)
    normals = relative / safe_r[:, None]

    # Build provenance hash from state
    state_hash = state.provenance_hash()

    for i in range(n):
        anchor = SpatialAnchor(
            position=state.positions[i].copy(),
            normal=normals[i].copy(),
            scale=float(state.radii[i]),
            source_cell_ids=[i],
            weights_to_cells=np.array([1.0]),
            provenance_hash=f"{state_hash}:cell_{i}",
        )

        node = PatchNode(
            node_id=i,
            node_type=NodeType.CELL_CENTER,
            anchor=anchor,
        )

        # Populate continuous state from CellGraphState
        if state.V_hair_cell.size > 0:
            node.V_hair_cell = float(state.V_hair_cell[i])
        if state.calcium.size > 0:
            node.calcium = float(state.calcium[i])
        if state.release_rate.size > 0:
            node.release_rate = float(state.release_rate[i])
        if state.V_afferent.size > 0:
            node.V_afferent = float(state.V_afferent[i])
        if state.met_open_probability.size > 0:
            node.met_open_prob = float(state.met_open_probability[i])

        # Populate afferent statistics if available
        if afferent_stats is not None:
            node.rate = float(afferent_stats["rate"][i])
            node.regularity = float(afferent_stats["regularity"][i])
            node.timing_precision = float(afferent_stats["timing_precision"][i])

        graph.nodes.append(node)

    # Build edges from contact graph
    if state.contact_graph is not None:
        for e_idx in range(state.contact_graph.num_edges):
            src, tgt = state.contact_graph.edges[e_idx]
            graph.edges.append(PatchEdge(
                source=int(src),
                target=int(tgt),
                edge_type=EdgeType.CONTACT,
                weight=1.0,
            ))

    return graph
