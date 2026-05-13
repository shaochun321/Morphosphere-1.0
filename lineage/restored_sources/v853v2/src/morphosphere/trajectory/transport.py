# Tags: [CORE_RUNTIME][TEMPORAL][SPATIAL]
# Role: Transport operator for cross-window node correspondence.
# Must Not: Import semantic_readout or legacy modules.
# Producers: pipeline
# Consumers: o_surface, band_records, origin
"""Transport Operator — cross-window node correspondence (v5 P05).

The transport operator establishes how nodes in window W_m
correspond to nodes in window W_{m+1}, enabling trajectory
stitching and continuity tracking.

This is the HIGHEST PRIORITY RISK package — without stable
transport, P/R freezing and origin anchoring cannot work reliably.

Φ_{m→m+1}: nodes(W_m) → nodes(W_{m+1})
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from morphosphere.core.types import Float64Array


@dataclass
class NodeCorrespondence:
    """Correspondence between a node in window m and window m+1."""
    source_node_id: str
    target_node_id: str
    distance: float = 0.0
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source_node_id,
            "target": self.target_node_id,
            "distance": self.distance,
            "confidence": self.confidence,
        }


@dataclass
class TransportOperator:
    """Cross-window transport operator Φ_{m→m+1} (v5 P05).

    Maps nodes from one time window to the next, enabling
    trajectory stitching and continuity analysis.

    Attributes:
        source_clock: clock_n of the source window
        target_clock: clock_n of the target window
        correspondences: node-to-node mappings
        transport_score: overall transport quality [0, 1]
        distortion: transport distortion measure
    """
    source_clock: int = 0
    target_clock: int = 0
    correspondences: list[NodeCorrespondence] = field(default_factory=list)
    transport_score: float = 0.0
    distortion: float = 0.0

    @property
    def num_correspondences(self) -> int:
        return len(self.correspondences)

    def get_target(self, source_id: str) -> str | None:
        """Get the target node ID for a source node."""
        for c in self.correspondences:
            if c.source_node_id == source_id:
                return c.target_node_id
        return None

    def mean_confidence(self) -> float:
        """Mean confidence across all correspondences."""
        if not self.correspondences:
            return 0.0
        return float(np.mean([c.confidence for c in self.correspondences]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_clock": self.source_clock,
            "target_clock": self.target_clock,
            "num_correspondences": self.num_correspondences,
            "transport_score": self.transport_score,
            "distortion": self.distortion,
            "mean_confidence": self.mean_confidence(),
            "correspondences": [c.to_dict() for c in self.correspondences],
        }


def compute_transport(
    source_positions: Float64Array,
    target_positions: Float64Array,
    source_node_ids: list[str],
    target_node_ids: list[str],
    *,
    source_clock: int = 0,
    target_clock: int = 0,
    max_distance: float | None = None,
) -> TransportOperator:
    """Compute the transport operator between two snapshots.

    Uses nearest-neighbor matching with distance-based confidence.
    In future versions, this could use optimal transport or
    registration algorithms.

    Args:
        source_positions: (N, 3) positions in source window
        target_positions: (M, 3) positions in target window
        source_node_ids: node IDs in source
        target_node_ids: node IDs in target
        max_distance: maximum allowed distance for a match
    """
    n_src = source_positions.shape[0]
    n_tgt = target_positions.shape[0]

    if n_src == 0 or n_tgt == 0:
        return TransportOperator(
            source_clock=source_clock,
            target_clock=target_clock,
        )

    # Build KD-tree on target positions
    tree = cKDTree(target_positions)
    distances, indices = tree.query(source_positions, k=1)

    # Compute adaptive max_distance if not provided
    if max_distance is None:
        # Use median of all pairwise distances as scale
        median_dist = float(np.median(distances))
        max_distance = max(3.0 * median_dist, 1e-6)

    correspondences: list[NodeCorrespondence] = []
    total_dist = 0.0
    for i in range(n_src):
        d = float(distances[i])
        j = int(indices[i])
        confidence = max(0.0, 1.0 - d / max_distance) if max_distance > 0 else 1.0

        correspondences.append(NodeCorrespondence(
            source_node_id=source_node_ids[i],
            target_node_id=target_node_ids[j],
            distance=d,
            confidence=confidence,
        ))
        total_dist += d

    # Transport score: fraction of high-confidence matches
    high_conf = sum(1 for c in correspondences if c.confidence > 0.5)
    transport_score = high_conf / max(n_src, 1)

    # Distortion: normalized mean distance
    mean_dist = total_dist / max(n_src, 1)
    characteristic_scale = float(np.std(source_positions)) if n_src > 1 else 1.0
    distortion = mean_dist / max(characteristic_scale, 1e-12)

    return TransportOperator(
        source_clock=source_clock,
        target_clock=target_clock,
        correspondences=correspondences,
        transport_score=transport_score,
        distortion=distortion,
    )


@dataclass
class TrajectoryStitcher:
    """Stitches trajectory segments across windows using transport operators.

    Maintains a history of transport operators and can reconstruct
    the full trajectory of any node across multiple windows.
    """
    operators: list[TransportOperator] = field(default_factory=list)

    def add_operator(self, op: TransportOperator) -> None:
        """Add a transport operator to the history."""
        self.operators.append(op)

    def trace_node(self, node_id: str) -> list[str]:
        """Trace a node through all transport steps.

        Returns the sequence of node IDs this node maps to.
        """
        trajectory = [node_id]
        current_id = node_id
        for op in self.operators:
            target = op.get_target(current_id)
            if target is None:
                break
            trajectory.append(target)
            current_id = target
        return trajectory

    def mean_transport_score(self) -> float:
        """Mean transport score across all operators."""
        if not self.operators:
            return 0.0
        return float(np.mean([op.transport_score for op in self.operators]))

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_operators": len(self.operators),
            "mean_transport_score": self.mean_transport_score(),
            "operators": [op.to_dict() for op in self.operators],
        }
