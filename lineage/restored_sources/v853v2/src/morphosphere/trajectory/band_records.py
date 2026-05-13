# Tags: [CORE_SCHEMA][CORE_RUNTIME][BAND][VERSIONED]
# Role: P/R band record objects — formal object system for decomposed components.
# Must Not: Import semantic_readout or legacy modules.
# Producers: decomposition pipeline
# Consumers: origin, transition, family_surface, ledger
"""P/R Band Records — formal object freezing (v5 P07).

PrimaryBandRecord: P_k as a first-class object (not a bare matrix)
ResidualBandRecord: R_k as a first-class object (not a leftover array)
OccupancyState: which nodes are occupied by P vs R vs unassigned

These replace the raw P/R arrays from TrajectoryDecomposition
with proper tracked objects that carry provenance and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import uuid


@dataclass
class PrimaryBandRecord:
    """Primary band record (p_band_record, v5 §P07).

    P_k is the main propagation / main energy subspace coherent support.
    It is a first-class object, NOT a bare matrix.

    Attributes:
        p_id: Unique identifier
        clock_start: Start tick
        clock_end: End tick
        member_node_ids: Nodes belonging to this P band
        core_margin_type: core | margin classification
        coherence_score: Coherence of this band
        bandwidth_score: Spectral bandwidth
        replay_support: Support from replay alignment
        provenance_support: Provenance chain quality
        origin_anchor_id: Reference to origin anchor bundle
    """
    p_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    member_node_ids: list[str] = field(default_factory=list)
    member_time_pairs: list[tuple[str, int]] = field(default_factory=list)
    core_margin_type: str = ""  # core | margin
    coherence_score: float = 0.0
    bandwidth_score: float = 0.0
    replay_support: float = 0.0
    provenance_support: float = 0.0
    origin_anchor_id: str = ""

    @property
    def size(self) -> int:
        return len(self.member_node_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "p_id": self.p_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "size": self.size,
            "member_node_ids": list(self.member_node_ids),
            "core_margin_type": self.core_margin_type,
            "coherence_score": self.coherence_score,
            "bandwidth_score": self.bandwidth_score,
            "replay_support": self.replay_support,
            "provenance_support": self.provenance_support,
            "origin_anchor_id": self.origin_anchor_id,
        }

    @classmethod
    def create(cls, **kwargs: Any) -> "PrimaryBandRecord":
        if "p_id" not in kwargs or not kwargs["p_id"]:
            kwargs["p_id"] = f"p_{uuid.uuid4().hex[:8]}"
        return cls(**kwargs)


@dataclass
class ResidualBandRecord:
    """Residual band record (r_band_record, v5 §P07).

    R_k represents residual / competing propagation / local anomalous
    active support relative to P_k.

    Attributes:
        r_id: Unique identifier
        margin_outer_type: margin | outer classification
        residual_reason: Why this is residual (boundary / competition / noise)
        routing_target: Where residual energy routes to
        upgrade_conditions: Conditions under which this could become P
        boundary_score: Boundary association score
        contradiction_score: Contradiction with P
    """
    r_id: str = ""
    clock_start: int = 0
    clock_end: int = 0
    member_node_ids: list[str] = field(default_factory=list)
    member_time_pairs: list[tuple[str, int]] = field(default_factory=list)
    margin_outer_type: str = ""  # margin | outer
    residual_reason: str = ""  # boundary | competition | noise | unknown
    routing_target: str = ""
    upgrade_conditions: str = ""
    boundary_score: float = 0.0
    contradiction_score: float = 0.0

    @property
    def size(self) -> int:
        return len(self.member_node_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "r_id": self.r_id,
            "clock_start": self.clock_start,
            "clock_end": self.clock_end,
            "size": self.size,
            "member_node_ids": list(self.member_node_ids),
            "margin_outer_type": self.margin_outer_type,
            "residual_reason": self.residual_reason,
            "routing_target": self.routing_target,
            "upgrade_conditions": self.upgrade_conditions,
            "boundary_score": self.boundary_score,
            "contradiction_score": self.contradiction_score,
        }

    @classmethod
    def create(cls, **kwargs: Any) -> "ResidualBandRecord":
        if "r_id" not in kwargs or not kwargs["r_id"]:
            kwargs["r_id"] = f"r_{uuid.uuid4().hex[:8]}"
        return cls(**kwargs)


@dataclass
class OccupancyState:
    """Node occupancy state — which nodes are P vs R vs unassigned (v5 §P07).

    Attributes:
        window_id: Associated analysis window
        p_nodes: Node IDs assigned to primary band
        r_nodes: Node IDs assigned to residual band
        unassigned_nodes: Node IDs not assigned to either
    """
    window_id: str = ""
    p_nodes: list[str] = field(default_factory=list)
    r_nodes: list[str] = field(default_factory=list)
    unassigned_nodes: list[str] = field(default_factory=list)

    @property
    def total_nodes(self) -> int:
        return len(self.p_nodes) + len(self.r_nodes) + len(self.unassigned_nodes)

    @property
    def p_fraction(self) -> float:
        total = self.total_nodes
        return len(self.p_nodes) / total if total > 0 else 0.0

    @property
    def r_fraction(self) -> float:
        total = self.total_nodes
        return len(self.r_nodes) / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "total_nodes": self.total_nodes,
            "p_nodes": len(self.p_nodes),
            "r_nodes": len(self.r_nodes),
            "unassigned": len(self.unassigned_nodes),
            "p_fraction": self.p_fraction,
            "r_fraction": self.r_fraction,
        }


@dataclass
class BoundaryElasticityRecord:
    """Boundary elasticity record (v5 §P08).

    Records how P/R boundaries respond to perturbations.
    """
    record_id: str = ""
    p_id: str = ""
    r_id: str = ""
    elasticity_score: float = 0.0
    boundary_stable: bool = True
    perturbation_type: str = ""
    delta_coherence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "p_id": self.p_id,
            "r_id": self.r_id,
            "elasticity_score": self.elasticity_score,
            "boundary_stable": self.boundary_stable,
            "perturbation_type": self.perturbation_type,
            "delta_coherence": self.delta_coherence,
        }


def freeze_bands_from_decomposition(
    *,
    P: Any,  # Float64Array
    R: Any,  # Float64Array
    node_ids: list[str],
    clock_start: int = 0,
    clock_end: int = 0,
    coherence_threshold: float = 0.3,
) -> tuple[PrimaryBandRecord, ResidualBandRecord, OccupancyState]:
    """Freeze P/R arrays into formal band record objects.

    This is the key upgrade: raw arrays → tracked objects with metadata.
    """
    import numpy as np

    n = len(node_ids)
    p_energy = np.sqrt(np.sum(P ** 2, axis=1)) if n > 0 else np.array([])
    r_energy = np.sqrt(np.sum(R ** 2, axis=1)) if n > 0 else np.array([])
    total = p_energy + r_energy + 1e-12

    # Classify nodes
    p_nodes = []
    r_nodes = []
    unassigned = []
    for i in range(n):
        p_frac = p_energy[i] / total[i]
        if p_frac > 1.0 - coherence_threshold:
            p_nodes.append(node_ids[i])
        elif p_frac < coherence_threshold:
            r_nodes.append(node_ids[i])
        else:
            unassigned.append(node_ids[i])

    p_record = PrimaryBandRecord.create(
        clock_start=clock_start,
        clock_end=clock_end,
        member_node_ids=p_nodes,
        core_margin_type="core" if len(p_nodes) > n // 2 else "margin",
        coherence_score=float(np.mean(p_energy[p_energy > 0])) if np.any(p_energy > 0) else 0.0,
    )

    r_record = ResidualBandRecord.create(
        clock_start=clock_start,
        clock_end=clock_end,
        member_node_ids=r_nodes,
        margin_outer_type="outer" if len(r_nodes) < n // 4 else "margin",
        residual_reason="unknown",
    )

    occupancy = OccupancyState(
        window_id=f"w_{clock_start}_{clock_end}",
        p_nodes=p_nodes,
        r_nodes=r_nodes,
        unassigned_nodes=unassigned,
    )

    return p_record, r_record, occupancy
