# Tags: [CORE_RUNTIME][TRAJECTORY][NEUTRAL]
# Role: Neutral observation matrix Y_k — no semantic content.
# Must Not: Import semantic_readout or produce semantic labels.
# Producers: preneural_slice
# Consumers: decomposition
"""WindowedTrajectoryField — neutral observation field (masterplan §8.1).

Y_k ∈ R^{N_points × D_state}, where each point contains:
    mech, strain, V_h, Ca, release, V_a, rate, regularity, timing_precision

This is a NEUTRAL observation field — no semantic labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from morphosphere.core.types import Float64Array
from morphosphere.preneural.preneural_slice import PreNeuralSlice


# Dimension names for the observation field
OBSERVATION_DIMS = [
    "mech_strain",
    "V_hair_cell",
    "calcium",
    "release_rate",
    "V_afferent",
    "rate",
    "regularity",
    "timing_precision",
]

D_STATE = len(OBSERVATION_DIMS)


@dataclass
class WindowedTrajectoryField:
    """Neutral observation field Y_k (masterplan §8.1).

    Y_k ∈ R^{N_points × D_state}

    Contains NO semantic labels. All naming (translation, rotation,
    onset, recovery, etc.) can only happen AFTER P/R decomposition.
    """
    t_start: float
    t_end: float
    positions: Float64Array     # (N, 3) spatial coordinates
    Y: Float64Array             # (N, D) state matrix
    provenance_hashes: list[str]  # per-point provenance
    source_slice_hash: str = ""

    @property
    def num_points(self) -> int:
        return self.Y.shape[0]

    @property
    def num_dims(self) -> int:
        return self.Y.shape[1] if self.Y.ndim == 2 else 0

    def normalize(self) -> "WindowedTrajectoryField":
        """Z-score normalize each dimension.

        Returns a new field with normalized Y. Preserves positions and provenance.
        """
        if self.num_points == 0:
            return self

        means = np.mean(self.Y, axis=0, keepdims=True)
        stds = np.std(self.Y, axis=0, keepdims=True)
        stds[stds < 1e-12] = 1.0
        Y_norm = (self.Y - means) / stds

        return WindowedTrajectoryField(
            t_start=self.t_start,
            t_end=self.t_end,
            positions=self.positions.copy(),
            Y=Y_norm,
            provenance_hashes=list(self.provenance_hashes),
            source_slice_hash=self.source_slice_hash,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "t_start": self.t_start,
            "t_end": self.t_end,
            "num_points": self.num_points,
            "num_dims": self.num_dims,
            "dim_names": OBSERVATION_DIMS[:self.num_dims],
            "source_slice_hash": self.source_slice_hash,
        }


def build_trajectory_field(slice_: PreNeuralSlice) -> WindowedTrajectoryField:
    """Build a WindowedTrajectoryField from a PreNeuralSlice.

    This extracts the pure state matrix from the slice, preserving
    positions and provenance for back-projection.
    """
    positions = slice_.positions_array()
    Y = slice_.state_matrix()
    hashes = [p.provenance_hash for p in slice_.points]

    return WindowedTrajectoryField(
        t_start=slice_.t_start,
        t_end=slice_.t_end,
        positions=positions,
        Y=Y,
        provenance_hashes=hashes,
        source_slice_hash=slice_.slice_hash,
    )
