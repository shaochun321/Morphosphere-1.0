"""MET channel model for the preneural layer.

Provides a higher-level view of the mechano-electrical transduction
channel that can be used by the patch graph for updating node states.
The low-level dynamics are in morphosphere.core.dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from morphosphere.core.types import METParams, Float64Array


@dataclass(frozen=True)
class METChannelState:
    """State of a single MET channel or patch."""
    deflection: float
    adaptation: float
    open_probability: float
    current: float

    def to_dict(self) -> dict[str, float]:
        return {
            "deflection": self.deflection,
            "adaptation": self.adaptation,
            "open_probability": self.open_probability,
            "current": self.current,
        }


def met_open_probability(
    deflection: float,
    adaptation: float,
    params: METParams,
) -> float:
    """Compute MET channel open probability.

    m_MET = sigmoid((b - b0 - a) / k_b)
    """
    x = (deflection - params.b0 - adaptation) / params.k_b
    if x >= 0:
        return 1.0 / (1.0 + np.exp(-x))
    z = np.exp(x)
    return float(z / (1.0 + z))
