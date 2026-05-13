# Tags: [CORE_RUNTIME][SPATIAL][VERSIONED]
# Role: Observable Surface (O_k) — field + candidate layers.
# Must Not: Import semantic_readout or legacy modules; no semantic labels.
# Producers: decomposition pipeline
# Consumers: band_records, origin
"""O-surface — Observable Surface layers (v5 P06).

The O-surface is split into two layers to prevent O_k from becoming
a catch-all:
  1. O_field_surface: per-node observability metrics
  2. O_candidate_surface: candidate clusters for P/R/origin

No semantic labels allowed in either layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from morphosphere.core.types import Float64Array


@dataclass
class ObservableFieldEntry:
    """Per-node observability metrics."""
    node_id: str = ""
    coherence: float = 0.0
    bandwidth: float = 0.0
    contradiction: float = 0.0
    transport_score: float = 0.0
    anchor_prior: float = 0.0
    p_candidate_energy: float = 0.0
    r_candidate_energy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "coherence": self.coherence,
            "bandwidth": self.bandwidth,
            "contradiction": self.contradiction,
            "transport_score": self.transport_score,
            "anchor_prior": self.anchor_prior,
            "p_candidate_energy": self.p_candidate_energy,
            "r_candidate_energy": self.r_candidate_energy,
        }


@dataclass
class ObservableFieldSurface:
    """Per-node observability field (O_field_surface, v5 P06).

    Contains metrics for each node describing how observable /
    coherent / contradictory its signal is. These metrics are
    computed from the trajectory field WITHOUT any semantic labels.
    """
    window_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    entries: list[ObservableFieldEntry] = field(default_factory=list)

    @property
    def num_nodes(self) -> int:
        return len(self.entries)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "num_nodes": self.num_nodes,
            "entries": [e.to_dict() for e in self.entries],
        }


@dataclass
class CandidateCluster:
    """A candidate cluster for P, R, or origin anchoring.

    Clusters are formed from spatially and temporally coherent
    groups of nodes with similar energy profiles.
    """
    cluster_id: str = ""
    cluster_type: str = ""  # p_candidate | r_candidate | origin_candidate
    node_members: list[str] = field(default_factory=list)
    window_members: list[str] = field(default_factory=list)
    support_score: float = 0.0
    mean_coherence: float = 0.0
    mean_energy: float = 0.0

    @property
    def size(self) -> int:
        return len(self.node_members)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "cluster_type": self.cluster_type,
            "size": self.size,
            "node_members": list(self.node_members),
            "window_members": list(self.window_members),
            "support_score": self.support_score,
            "mean_coherence": self.mean_coherence,
            "mean_energy": self.mean_energy,
        }


@dataclass
class ObservableCandidateSurface:
    """Candidate surface (O_candidate_surface, v5 P06).

    Contains candidate clusters formed from the field surface.
    Each cluster must trace back to its source field entries.
    """
    window_id: str = ""
    p_candidates: list[CandidateCluster] = field(default_factory=list)
    r_candidates: list[CandidateCluster] = field(default_factory=list)
    origin_candidates: list[CandidateCluster] = field(default_factory=list)

    @property
    def total_candidates(self) -> int:
        return len(self.p_candidates) + len(self.r_candidates) + len(self.origin_candidates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "total_candidates": self.total_candidates,
            "p_candidates": [c.to_dict() for c in self.p_candidates],
            "r_candidates": [c.to_dict() for c in self.r_candidates],
            "origin_candidates": [c.to_dict() for c in self.origin_candidates],
        }


@dataclass
class ObservableSurface:
    """Combined O_k = field + candidate (v5 P06).

    This is the top-level observable surface that wraps both layers.
    No semantic labels are stored here — this is purely structural.
    """
    window_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    field_surface: ObservableFieldSurface | None = None
    candidate_surface: ObservableCandidateSurface | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "field_surface": self.field_surface.to_dict() if self.field_surface else None,
            "candidate_surface": self.candidate_surface.to_dict() if self.candidate_surface else None,
        }


def build_observable_surface(
    *,
    positions: Float64Array,
    P: Float64Array,
    R: Float64Array,
    node_ids: list[str],
    window_id: str = "",
    clock_start: int = 0,
    clock_end: int = 0,
    transport_scores: Float64Array | None = None,
) -> ObservableSurface:
    """Build an ObservableSurface from decomposition results.

    Computes per-node observability metrics and identifies candidate
    clusters for P, R, and origin.
    """
    n = positions.shape[0]
    if n == 0:
        return ObservableSurface(window_id=window_id, clock_start=clock_start, clock_end=clock_end)

    # Compute per-node metrics
    p_energy = np.sqrt(np.sum(P ** 2, axis=1))
    r_energy = np.sqrt(np.sum(R ** 2, axis=1))
    total_energy = p_energy + r_energy + 1e-12

    if transport_scores is None:
        transport_scores = np.ones(n)

    entries: list[ObservableFieldEntry] = []
    for i in range(n):
        coherence = float(p_energy[i] / total_energy[i])
        contradiction = float(r_energy[i] / total_energy[i])
        entries.append(ObservableFieldEntry(
            node_id=node_ids[i],
            coherence=coherence,
            bandwidth=float(np.std(P[i])) if P.shape[1] > 1 else 0.0,
            contradiction=contradiction,
            transport_score=float(transport_scores[i]),
            anchor_prior=coherence * float(transport_scores[i]),
            p_candidate_energy=float(p_energy[i]),
            r_candidate_energy=float(r_energy[i]),
        ))

    field_surface = ObservableFieldSurface(
        window_id=window_id,
        clock_start=clock_start,
        clock_end=clock_end,
        entries=entries,
    )

    # Build candidate clusters
    p_threshold = np.mean(p_energy) + 0.5 * np.std(p_energy)
    r_threshold = np.mean(r_energy) + 1.0 * np.std(r_energy)

    p_mask = p_energy > p_threshold
    r_mask = r_energy > r_threshold

    p_candidates: list[CandidateCluster] = []
    if np.any(p_mask):
        p_members = [node_ids[i] for i in range(n) if p_mask[i]]
        p_candidates.append(CandidateCluster(
            cluster_id=f"pc_{window_id}_0",
            cluster_type="p_candidate",
            node_members=p_members,
            support_score=float(np.mean(p_energy[p_mask])),
            mean_coherence=float(np.mean([entries[i].coherence for i in range(n) if p_mask[i]])),
            mean_energy=float(np.mean(p_energy[p_mask])),
        ))

    r_candidates: list[CandidateCluster] = []
    if np.any(r_mask):
        r_members = [node_ids[i] for i in range(n) if r_mask[i]]
        r_candidates.append(CandidateCluster(
            cluster_id=f"rc_{window_id}_0",
            cluster_type="r_candidate",
            node_members=r_members,
            support_score=float(np.mean(r_energy[r_mask])),
            mean_coherence=float(np.mean([entries[i].coherence for i in range(n) if r_mask[i]])),
            mean_energy=float(np.mean(r_energy[r_mask])),
        ))

    # Origin candidates: high coherence + high transport score
    origin_threshold = 0.6
    origin_mask = np.array([e.anchor_prior > origin_threshold for e in entries])
    origin_candidates: list[CandidateCluster] = []
    if np.any(origin_mask):
        o_members = [node_ids[i] for i in range(n) if origin_mask[i]]
        origin_candidates.append(CandidateCluster(
            cluster_id=f"oc_{window_id}_0",
            cluster_type="origin_candidate",
            node_members=o_members,
            support_score=float(np.mean([entries[i].anchor_prior for i in range(n) if origin_mask[i]])),
        ))

    candidate_surface = ObservableCandidateSurface(
        window_id=window_id,
        p_candidates=p_candidates,
        r_candidates=r_candidates,
        origin_candidates=origin_candidates,
    )

    return ObservableSurface(
        window_id=window_id,
        clock_start=clock_start,
        clock_end=clock_end,
        field_surface=field_surface,
        candidate_surface=candidate_surface,
    )
