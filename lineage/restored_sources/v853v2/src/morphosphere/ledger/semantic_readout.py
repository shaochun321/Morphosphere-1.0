# Tags: [SEMANTIC_READOUT][POST_HOC][READ_ONLY]
# Role: Post-hoc labeling only. The ONLY place for semantic labels.
# Must Not: Write labels back into core, preneural, or trajectory layers.
# Producers: decomposition results
# Consumers: user-facing output, audit
"""Semantic Readout Surface — post-hoc labeling only (masterplan §4).

The Semantic Readout Surface is the ONLY place where labels like
"translation_like", "rotation_like", "onset", "recovery" are produced.
These labels are applied POST-HOC to already-decomposed P/R structures.

They NEVER feed back into the active runtime path.

Masterplan §3: "内部中性、外部语义"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from morphosphere.core.types import Float64Array
from morphosphere.trajectory.decomposition import TrajectoryDecomposition


@dataclass
class SemanticLabel:
    """A single semantic label applied to a decomposition component."""
    label_name: str
    confidence: float = 0.0
    support_fraction: float = 0.0
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label_name": self.label_name,
            "confidence": self.confidence,
            "support_fraction": self.support_fraction,
            "evidence": dict(self.evidence),
        }


@dataclass
class SemanticReadout:
    """Post-hoc semantic readout of a trajectory decomposition.

    Labels are produced by analyzing P_k and R_k AFTER decomposition.
    They are purely descriptive and do not modify any upstream state.
    """
    time: float
    p_labels: list[SemanticLabel] = field(default_factory=list)
    r_labels: list[SemanticLabel] = field(default_factory=list)
    dominant_mode: str = "unknown"
    readout_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "dominant_mode": self.dominant_mode,
            "readout_hash": self.readout_hash,
            "p_labels": [l.to_dict() for l in self.p_labels],
            "r_labels": [l.to_dict() for l in self.r_labels],
        }


def compute_semantic_readout(decomposition: TrajectoryDecomposition) -> SemanticReadout:
    """Produce semantic labels from a trajectory decomposition.

    This is the ONLY function that generates semantic labels.
    Labels are based on spatial patterns in P and R components.

    Masterplan §8.2: "先分离结构，再命名结构"
    """
    readout = SemanticReadout(time=decomposition.t_end)

    if decomposition.num_points == 0:
        return readout

    P = decomposition.P
    R = decomposition.R
    positions = decomposition.positions

    # ── Analyze P component: look for coherent spatial patterns ──────────

    # Check for translation-like pattern: gradient along a spatial axis
    p_labels: list[SemanticLabel] = []
    for axis_idx, axis_name in enumerate(["x", "y", "z"]):
        if positions.shape[0] < 2:
            continue
        # Correlation between spatial position and P energy
        p_energy = np.sqrt(np.sum(P ** 2, axis=1))
        spatial_coord = positions[:, axis_idx]

        if np.std(spatial_coord) > 1e-12 and np.std(p_energy) > 1e-12:
            corr = np.corrcoef(spatial_coord, p_energy)[0, 1]
            if abs(corr) > 0.3:
                p_labels.append(SemanticLabel(
                    label_name=f"gradient_along_{axis_name}",
                    confidence=abs(corr),
                    support_fraction=float(np.mean(p_energy > np.median(p_energy))),
                    evidence={"correlation": float(corr), "axis": axis_name},
                ))

    # Check for radial pattern
    center = np.mean(positions, axis=0)
    radii = np.linalg.norm(positions - center, axis=1)
    p_energy = np.sqrt(np.sum(P ** 2, axis=1))
    if np.std(radii) > 1e-12 and np.std(p_energy) > 1e-12:
        radial_corr = np.corrcoef(radii, p_energy)[0, 1]
        if abs(radial_corr) > 0.3:
            p_labels.append(SemanticLabel(
                label_name="radial_pattern",
                confidence=abs(radial_corr),
                support_fraction=float(np.mean(p_energy > np.median(p_energy))),
                evidence={"radial_correlation": float(radial_corr)},
            ))

    # ── Analyze R component: look for sparse local anomalies ──────────

    r_labels: list[SemanticLabel] = []
    r_energy = np.sqrt(np.sum(R ** 2, axis=1))
    if np.max(r_energy) > 1e-12:
        # Find hotspots
        threshold = np.mean(r_energy) + 2.0 * np.std(r_energy)
        hotspot_mask = r_energy > threshold
        hotspot_fraction = float(np.mean(hotspot_mask))

        if hotspot_fraction > 0.01:
            r_labels.append(SemanticLabel(
                label_name="local_anomaly",
                confidence=float(np.max(r_energy) / (np.mean(r_energy) + 1e-12)),
                support_fraction=hotspot_fraction,
                evidence={"num_hotspots": int(np.sum(hotspot_mask))},
            ))

    readout.p_labels = p_labels
    readout.r_labels = r_labels

    # Determine dominant mode
    coherence = decomposition.coherence_score()
    if coherence > 0.7:
        if p_labels:
            readout.dominant_mode = p_labels[0].label_name
        else:
            readout.dominant_mode = "coherent_unclassified"
    elif coherence < 0.3:
        readout.dominant_mode = "residual_dominated"
    else:
        readout.dominant_mode = "mixed"

    return readout
