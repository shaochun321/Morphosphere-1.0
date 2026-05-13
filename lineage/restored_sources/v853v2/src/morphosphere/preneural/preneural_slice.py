"""PreNeuralSlice — contract and analysis view (masterplan §7.2).

A PreNeuralSlice P[t-Δ,t] represents a time-windowed, back-projectable
3D topological point set. It is the contract/analysis view of the same
preneural carrier layer that PatchAfferentTransmissionGraph organizes
at runtime.

Key property: every point in the slice can be traced back (回投) to
its originating cell(s) via provenance information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib

import numpy as np

from morphosphere.core.types import Float64Array, SpatialAnchor
from morphosphere.core.schema import GeometryNode, SignalWindow, SignalWindowEntry
from .patch_graph import PatchAfferentTransmissionGraph, PatchNode


@dataclass
class SlicePoint:
    """A single point in the PreNeuralSlice.

    Each point carries full provenance back to the originating patch/cell.
    """
    point_id: int
    position: Float64Array           # (3,) xyz
    normal: Float64Array             # (3,) outward normal
    source_patch_ids: list[int]      # originating patch node IDs
    weights_to_patches: Float64Array # (len(source_patch_ids),) weights
    provenance_hash: str

    # State dimensions for observation field (masterplan §8.1)
    mech_strain: float = 0.0
    V_hair_cell: float = -65.0
    calcium: float = 0.0
    release_rate: float = 0.0
    V_afferent: float = -70.0
    rate: float = 0.0
    regularity: float = 0.0
    timing_precision: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "point_id": self.point_id,
            "position": self.position.tolist(),
            "normal": self.normal.tolist(),
            "source_patch_ids": self.source_patch_ids,
            "weights_to_patches": self.weights_to_patches.tolist(),
            "provenance_hash": self.provenance_hash,
            "mech_strain": self.mech_strain,
            "V_hair_cell": self.V_hair_cell,
            "calcium": self.calcium,
            "release_rate": self.release_rate,
            "V_afferent": self.V_afferent,
            "rate": self.rate,
            "regularity": self.regularity,
            "timing_precision": self.timing_precision,
        }


@dataclass
class PreNeuralSlice:
    """Time-windowed, back-projectable 3D topological point set.

    Masterplan §7.2: Slice contract.
    The slice represents the state of the preneural layer over the
    window [t_start, t_end], organized as a set of points with full
    provenance and state information.
    """
    t_start: float
    t_end: float
    clock_start: int = 0
    clock_end: int = 0
    window_id: str = ""
    points: list[SlicePoint] = field(default_factory=list)
    slice_hash: str = ""

    @property
    def num_points(self) -> int:
        return len(self.points)

    @property
    def duration(self) -> float:
        return self.t_end - self.t_start

    def positions_array(self) -> Float64Array:
        """Extract (N, 3) position array for analysis."""
        if not self.points:
            return np.empty((0, 3))
        return np.array([p.position for p in self.points])

    def state_matrix(self) -> Float64Array:
        """Extract (N, D) state matrix for trajectory field construction.

        Columns: mech_strain, V_h, Ca, release, V_aff, rate, regularity, precision
        This feeds directly into WindowedTrajectoryField (masterplan §8.1).
        """
        if not self.points:
            return np.empty((0, 8))
        return np.array([
            [p.mech_strain, p.V_hair_cell, p.calcium, p.release_rate,
             p.V_afferent, p.rate, p.regularity, p.timing_precision]
            for p in self.points
        ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "t_start": self.t_start,
            "t_end": self.t_end,
            "num_points": self.num_points,
            "slice_hash": self.slice_hash,
            "points": [p.to_dict() for p in self.points],
        }

    def compute_hash(self) -> str:
        """Compute content hash for provenance tracking."""
        h = hashlib.sha256()
        h.update(f"t={self.t_start:.8f}-{self.t_end:.8f}".encode())
        for p in self.points:
            h.update(p.position.tobytes())
            h.update(f"{p.V_hair_cell:.6f}".encode())
        self.slice_hash = h.hexdigest()[:16]
        return self.slice_hash


def build_slice_from_graph(
    graph: PatchAfferentTransmissionGraph,
    t_start: float,
    t_end: float,
) -> PreNeuralSlice:
    """Build a PreNeuralSlice from a PatchAfferentTransmissionGraph snapshot.

    This is the "同一承载层的两种视图" bridge: runtime graph → analysis slice.
    """
    slice_ = PreNeuralSlice(t_start=t_start, t_end=t_end)

    for node in graph.nodes:
        point = SlicePoint(
            point_id=node.node_id,
            position=node.anchor.position.copy(),
            normal=node.anchor.normal.copy(),
            source_patch_ids=[node.node_id],
            weights_to_patches=np.array([1.0]),
            provenance_hash=node.anchor.provenance_hash,
            mech_strain=0.0,  # will be populated from state
            V_hair_cell=node.V_hair_cell,
            calcium=node.calcium,
            release_rate=node.release_rate,
            V_afferent=node.V_afferent,
            rate=node.rate,
            regularity=node.regularity,
            timing_precision=node.timing_precision,
        )
        slice_.points.append(point)

    slice_.compute_hash()
    return slice_


@dataclass
class PreNeuralPointSetSlice:
    """Full v5 PreNeuralPointSetSlice = Geometry + Signal (v5 P04-P05).

    This is the upgraded version that combines:
      - PreNeuralGeometry: spatial anchors with provenance
      - SignalWindow: time-windowed signal aggregation

    T_k = {G_k, S_k, Topology_k}
    """
    clock_start: int = 0
    clock_end: int = 0
    window_id: str = ""
    run_id: str = ""

    # Geometry view: node positions + provenance
    geometry_nodes: list[GeometryNode] = field(default_factory=list)

    # Signal view: per-node state values
    signal_window: SignalWindow | None = None

    # Legacy compatibility: also keep points for backward compat
    points: list[SlicePoint] = field(default_factory=list)
    slice_hash: str = ""

    @property
    def num_points(self) -> int:
        return len(self.geometry_nodes) if self.geometry_nodes else len(self.points)

    def positions_array(self) -> Float64Array:
        """Extract (N, 3) position array."""
        if self.geometry_nodes:
            return np.array([n.xyz for n in self.geometry_nodes])
        if self.points:
            return np.array([p.position for p in self.points])
        return np.empty((0, 3))

    def state_matrix(self) -> Float64Array:
        """Extract (N, D) state matrix.

        Uses SignalWindow if available, otherwise falls back to points.
        """
        if self.signal_window and self.signal_window.entries:
            return self.signal_window.to_matrix()
        if self.points:
            return np.array([
                [p.mech_strain, p.V_hair_cell, p.calcium, p.release_rate,
                 p.V_afferent, p.rate, p.regularity, p.timing_precision]
                for p in self.points
            ])
        return np.empty((0, 8))

    def provenance_hashes(self) -> list[str]:
        """Get per-point provenance hashes."""
        if self.geometry_nodes:
            return [n.provenance_hash for n in self.geometry_nodes]
        return [p.provenance_hash for p in self.points]

    def source_cell_ids(self) -> list[list[int]]:
        """Get per-point source cell IDs for back-projection."""
        if self.geometry_nodes:
            return [list(n.source_cell_ids) for n in self.geometry_nodes]
        return [list(p.source_patch_ids) for p in self.points]

    def validate(self) -> list[str]:
        """Check invariants."""
        errors: list[str] = []
        if self.geometry_nodes:
            for n in self.geometry_nodes:
                errors.extend(n.validate())
        if self.signal_window:
            n_geo = len(self.geometry_nodes)
            n_sig = self.signal_window.num_nodes
            if n_geo > 0 and n_sig > 0 and n_geo != n_sig:
                errors.append(
                    f"Geometry nodes ({n_geo}) != signal entries ({n_sig})"
                )
        return errors

    def compute_hash(self) -> str:
        """Compute content hash."""
        h = hashlib.sha256()
        h.update(f"w={self.window_id}".encode())
        h.update(f"c={self.clock_start}-{self.clock_end}".encode())
        for node in self.geometry_nodes:
            h.update(node.xyz.tobytes())
        self.slice_hash = h.hexdigest()[:16]
        return self.slice_hash

    def to_dict(self) -> dict[str, Any]:
        return {
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "window_id": self.window_id,
            "run_id": self.run_id,
            "num_points": self.num_points,
            "slice_hash": self.slice_hash,
        }


class PreNeuralSliceAccumulator:
    """Accumulates graph snapshots over a time window to build a slice.

    For the first version, we simply use the latest snapshot.
    Extension point for time-averaged or windowed analysis.
    """

    def __init__(self, window_duration: float = 0.1):
        self.window_duration = window_duration
        self._snapshots: list[PatchAfferentTransmissionGraph] = []

    def ingest(self, graph: PatchAfferentTransmissionGraph) -> None:
        self._snapshots.append(graph)
        # Prune snapshots outside the window
        if self._snapshots:
            t_cutoff = graph.time - self.window_duration
            self._snapshots = [s for s in self._snapshots if s.time >= t_cutoff]

    def build_slice(self) -> PreNeuralSlice | None:
        """Build a slice from accumulated snapshots."""
        if not self._snapshots:
            return None

        latest = self._snapshots[-1]
        t_end = latest.time
        t_start = max(t_end - self.window_duration, 0.0)

        return build_slice_from_graph(latest, t_start, t_end)
