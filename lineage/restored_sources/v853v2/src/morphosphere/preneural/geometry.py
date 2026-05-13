# Tags: [CORE_RUNTIME][SPATIAL][VERSIONED]
# Role: PreNeuralGeometry — builds GeometryNode registrations from CellGraphState.
# Must Not: Import semantic_readout or legacy modules.
# Producers: pipeline, patch_graph
# Consumers: preneural_slice, transport, o_surface
"""PreNeuralGeometry — geometry anchor registration (v5 P04).

Builds GeometryNode objects from CellGraphState, providing spatial
anchors with full provenance for the preneural carrier layer.

Every node can be back-traced to its originating cell(s).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib

import numpy as np

from morphosphere.core.cell_graph_state import CellGraphState
from morphosphere.core.schema import GeometryNode, TopologySnapshot, TopologyEdge


@dataclass
class PreNeuralGeometry:
    """Geometry registration for the preneural carrier layer (v5 §P04).

    Contains all GeometryNode objects for a given clock tick,
    plus the TopologySnapshot describing their connectivity.

    Invariants:
        - Every node has source_cell_ids or source_patch_ids
        - Topology edges match actual node IDs
        - All nodes have valid 3D coordinates
    """
    clock_n: int = 0
    run_id: str = ""
    nodes: list[GeometryNode] = field(default_factory=list)
    topology: TopologySnapshot | None = None
    geometry_hash: str = ""

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    def node_by_id(self, node_id: str) -> GeometryNode | None:
        """Look up a node by ID."""
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def positions_array(self) -> np.ndarray:
        """Extract (N, 3) position array."""
        if not self.nodes:
            return np.empty((0, 3))
        return np.array([n.xyz for n in self.nodes])

    def validate(self) -> list[str]:
        """Check invariants."""
        errors: list[str] = []
        node_ids = set()
        for n in self.nodes:
            errors.extend(n.validate())
            if n.node_id in node_ids:
                errors.append(f"Duplicate node_id: {n.node_id}")
            node_ids.add(n.node_id)

        # Check topology edges reference valid nodes
        if self.topology:
            for e in self.topology.edges:
                if e.u not in node_ids:
                    errors.append(f"Topology edge references unknown node: {e.u}")
                if e.v not in node_ids:
                    errors.append(f"Topology edge references unknown node: {e.v}")
        return errors

    def compute_hash(self) -> str:
        """Compute content hash."""
        h = hashlib.sha256()
        h.update(f"clock_n={self.clock_n}".encode())
        for n in self.nodes:
            h.update(n.node_id.encode())
            h.update(n.xyz.tobytes())
        self.geometry_hash = h.hexdigest()[:16]
        return self.geometry_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_n": self.clock_n,
            "run_id": self.run_id,
            "num_nodes": self.num_nodes,
            "geometry_hash": self.geometry_hash,
            "nodes": [n.to_dict() for n in self.nodes],
            "topology": self.topology.to_dict() if self.topology else None,
        }


def build_geometry_from_state(
    state: CellGraphState,
) -> PreNeuralGeometry:
    """Build PreNeuralGeometry from CellGraphState.

    Creates one GeometryNode per cell (first-version surrogate).
    In future versions, cells can be aggregated into membrane patches.
    """
    n = state.num_cells
    center = np.mean(state.positions, axis=0)
    relative = state.positions - center
    radius = np.linalg.norm(relative, axis=1)
    safe_r = np.maximum(radius, 1e-12)
    normals = relative / safe_r[:, None]

    # Compute boundary distances (distance from outer edge)
    max_r = np.max(radius) if n > 0 else 1.0
    boundary_distances = max_r - radius

    # Base provenance hash from state
    state_hash = state.provenance_hash()

    nodes: list[GeometryNode] = []
    for i in range(n):
        node = GeometryNode(
            node_id=f"c{i}",
            node_type="cell_center",
            xyz=state.positions[i].copy(),
            local_normal=normals[i].copy(),
            support_radius=float(state.radii[i]),
            boundary_distance=float(boundary_distances[i]),
            source_cell_ids=[i],
            source_patch_ids=[],
            provenance_hash=f"{state_hash}:c{i}",
        )
        nodes.append(node)

    # Build topology from contact graph
    topo_edges: list[TopologyEdge] = []
    if state.contact_graph is not None:
        for e_idx in range(state.contact_graph.num_edges):
            src, tgt = state.contact_graph.edges[e_idx]
            topo_edges.append(TopologyEdge(
                u=f"c{int(src)}",
                v=f"c{int(tgt)}",
                edge_type="contact",
                weight=1.0,
            ))

    # Set neighbor_node_ids on each geometry node
    adjacency: dict[str, list[str]] = {f"c{i}": [] for i in range(n)}
    for te in topo_edges:
        adjacency[te.u].append(te.v)
        adjacency[te.v].append(te.u)
    for node in nodes:
        node.neighbor_node_ids = adjacency.get(node.node_id, [])

    topology = TopologySnapshot(
        clock_n=state.clock_n,
        edges=topo_edges,
    )
    topology.compute_hash()

    geometry = PreNeuralGeometry(
        clock_n=state.clock_n,
        run_id=state.run_id,
        nodes=nodes,
        topology=topology,
    )
    geometry.compute_hash()

    return geometry
