# Tags: [CORE_SCHEMA][CORE_RUNTIME][SPATIAL][VERSIONED]
# Role: Defines GeometryNode, TopologySnapshot, and SignalWindow objects
#       for the v5 object system (v5 §3.2, §3.3).
# Must Not: Import semantic_readout or legacy modules.
# Producers: patch_graph.builder, signal_window.builder
# Consumers: preneural, transport, o_surface, band_records
"""Core schema objects for the v5 object system.

GeometryNode — spatial anchor point in the preneural carrier layer
TopologySnapshot — graph connectivity at a given clock tick
SignalWindow — time-windowed signal aggregation per node

These are the building blocks for PreNeuralPointSetSlice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib

import numpy as np
from numpy.typing import NDArray

Float64Array = NDArray[np.float64]


# ── GeometryNode ────────────────────────────────────────────────────────────

@dataclass
class GeometryNode:
    """Spatial anchor point in the preneural carrier layer (v5 §3.2.1).

    Invariants:
        - source_cell_ids or source_patch_ids must be non-empty
        - neighbor_node_ids are topological adjacency, not arbitrary kNN
        - Every node must be back-traceable to source objects

    Attributes:
        node_id: Unique identifier
        node_type: cell_center | membrane_patch | synapse_patch | afferent_terminal
        xyz: 3D position in lab frame
        local_normal: outward normal vector (or None)
        support_radius: characteristic length scale
        boundary_distance: distance to nearest boundary
        source_cell_ids: originating cell indices
        source_patch_ids: originating patch indices
        neighbor_node_ids: topological neighbors
        provenance_hash: for replay alignment
        geometry_version: schema version string
    """
    node_id: str = ""
    node_type: str = "cell_center"  # cell_center | membrane_patch | synapse_patch | afferent_terminal
    xyz: Float64Array = field(default_factory=lambda: np.zeros(3))
    local_normal: Float64Array | None = None
    support_radius: float = 0.004
    boundary_distance: float = 0.0
    source_cell_ids: list[int] = field(default_factory=list)
    source_patch_ids: list[int] = field(default_factory=list)
    neighbor_node_ids: list[str] = field(default_factory=list)
    provenance_hash: str = ""
    geometry_version: str = "1.0.0"

    def validate(self) -> list[str]:
        """Check invariants."""
        errors: list[str] = []
        if not self.source_cell_ids and not self.source_patch_ids:
            errors.append("At least one of source_cell_ids or source_patch_ids must be non-empty")
        if self.xyz.shape != (3,):
            errors.append(f"xyz must be shape (3,), got {self.xyz.shape}")
        if self.local_normal is not None and self.local_normal.shape != (3,):
            errors.append(f"local_normal must be shape (3,), got {self.local_normal.shape}")
        valid_types = {"cell_center", "membrane_patch", "synapse_patch", "afferent_terminal"}
        if self.node_type not in valid_types:
            errors.append(f"node_type must be one of {valid_types}, got '{self.node_type}'")
        return errors

    def compute_provenance_hash(self) -> str:
        """Compute content hash for provenance tracking."""
        h = hashlib.sha256()
        h.update(self.node_id.encode())
        h.update(self.xyz.tobytes())
        h.update(str(self.source_cell_ids).encode())
        h.update(str(self.source_patch_ids).encode())
        self.provenance_hash = h.hexdigest()[:16]
        return self.provenance_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "xyz": self.xyz.tolist(),
            "local_normal": self.local_normal.tolist() if self.local_normal is not None else None,
            "support_radius": self.support_radius,
            "boundary_distance": self.boundary_distance,
            "source_cell_ids": list(self.source_cell_ids),
            "source_patch_ids": list(self.source_patch_ids),
            "neighbor_node_ids": list(self.neighbor_node_ids),
            "provenance_hash": self.provenance_hash,
            "geometry_version": self.geometry_version,
        }


# ── TopologySnapshot ────────────────────────────────────────────────────────

@dataclass
class TopologyEdge:
    """A single edge in the TopologySnapshot."""
    u: str
    v: str
    edge_type: str = "contact"  # contact | synapse | functional | spatial | transport_hint
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "u": self.u,
            "v": self.v,
            "edge_type": self.edge_type,
            "weight": self.weight,
        }


@dataclass
class TopologySnapshot:
    """Graph connectivity at a given clock tick (v5 §3.2.2).

    Attributes:
        clock_n: The clock tick this snapshot corresponds to
        edges: List of edges
        laplacian_cache_ref: Reference to cached Laplacian matrix
        topology_hash: Content hash for provenance
    """
    clock_n: int = 0
    edges: list[TopologyEdge] = field(default_factory=list)
    laplacian_cache_ref: str = ""
    topology_hash: str = ""

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    def node_ids(self) -> set[str]:
        """Get all unique node IDs in the topology."""
        ids: set[str] = set()
        for e in self.edges:
            ids.add(e.u)
            ids.add(e.v)
        return ids

    def adjacency(self, node_id: str) -> list[str]:
        """Get neighbors of a node."""
        neighbors: list[str] = []
        for e in self.edges:
            if e.u == node_id:
                neighbors.append(e.v)
            elif e.v == node_id:
                neighbors.append(e.u)
        return neighbors

    def compute_hash(self) -> str:
        """Compute content hash."""
        h = hashlib.sha256()
        h.update(f"clock_n={self.clock_n}".encode())
        for e in sorted(self.edges, key=lambda x: (x.u, x.v)):
            h.update(f"{e.u}-{e.v}-{e.edge_type}".encode())
        self.topology_hash = h.hexdigest()[:16]
        return self.topology_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_n": self.clock_n,
            "num_edges": self.num_edges,
            "edges": [e.to_dict() for e in self.edges],
            "laplacian_cache_ref": self.laplacian_cache_ref,
            "topology_hash": self.topology_hash,
        }


# ── SignalWindow ────────────────────────────────────────────────────────────

@dataclass
class SignalWindowEntry:
    """Signal values for a single node within a window."""
    node_id: str = ""
    V_mean: float = -65.0
    V_slope: float = 0.0
    release_proxy: float = 0.0
    afferent_current: float = 0.0
    spike_rate: float = 0.0
    spike_regularity: float = 0.0
    timing_precision: float = 0.0
    adaptation_state: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "V_mean": self.V_mean,
            "V_slope": self.V_slope,
            "release_proxy": self.release_proxy,
            "afferent_current": self.afferent_current,
            "spike_rate": self.spike_rate,
            "spike_regularity": self.spike_regularity,
            "timing_precision": self.timing_precision,
            "adaptation_state": self.adaptation_state,
        }

    def to_array(self) -> Float64Array:
        """Convert to numeric array for matrix operations."""
        return np.array([
            self.V_mean, self.V_slope, self.release_proxy,
            self.afferent_current, self.spike_rate, self.spike_regularity,
            self.timing_precision, self.adaptation_state,
        ], dtype=np.float64)


@dataclass
class SignalWindow:
    """Time-windowed signal aggregation per node (v5 §3.3).

    Attributes:
        window_id: Reference to the AnalysisWindow
        clock_start: Start tick
        clock_end: End tick
        entries: Per-node signal values
    """
    window_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    entries: list[SignalWindowEntry] = field(default_factory=list)

    @property
    def num_nodes(self) -> int:
        return len(self.entries)

    def to_matrix(self) -> Float64Array:
        """Convert to (N, D) matrix for downstream use."""
        if not self.entries:
            return np.empty((0, 8), dtype=np.float64)
        return np.array([e.to_array() for e in self.entries], dtype=np.float64)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "num_nodes": self.num_nodes,
            "entries": [e.to_dict() for e in self.entries],
        }
