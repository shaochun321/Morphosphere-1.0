"""Threshold configuration for the freezing phase (V8 §8.7-8.8).

Replaces bare constants with a ThresholdProfile dataclass that supports
version-frozen vs configurable threshold sets.
"""
from dataclasses import dataclass


@dataclass
class ThresholdProfile:
    """V8 §8.7: Explicit threshold profile for P/R candidate evaluation.

    theta_P:        Main propagation candidate energy threshold
    theta_kappa:    Local consistency threshold (coherent propagation ridge)
    theta_bw:       High-frequency exclusion threshold (spectral content limit)
    theta_R:        Residual local high-energy threshold
    theta_boundary: Boundary fragility threshold (prevents boundary artifacts)
    theta_contra:   Contradiction threshold for mixed-state detection
    epsilon_transport: Transport error tolerance for P freezing
    rho_radius:     Support radius for spatial locality checks
    """
    theta_P: float = 0.8
    theta_kappa: float = 0.5
    theta_bw: float = 0.3
    theta_R: float = 0.6
    theta_boundary: float = 0.7
    theta_contra: float = 0.4
    epsilon_transport: float = 0.05
    rho_radius: float = 5.0

    @classmethod
    def default(cls) -> "ThresholdProfile":
        """Return default threshold profile."""
        return cls()

    @classmethod
    def relaxed(cls) -> "ThresholdProfile":
        """Return relaxed thresholds for exploratory runs."""
        return cls(
            theta_P=0.5,
            theta_kappa=0.3,
            theta_bw=0.5,
            theta_R=0.4,
            theta_boundary=0.5,
            theta_contra=0.3,
            epsilon_transport=0.1,
            rho_radius=8.0,
        )

    @classmethod
    def strict(cls) -> "ThresholdProfile":
        """Return strict thresholds for production/frozen runs."""
        return cls(
            theta_P=0.9,
            theta_kappa=0.7,
            theta_bw=0.2,
            theta_R=0.8,
            theta_boundary=0.85,
            theta_contra=0.5,
            epsilon_transport=0.02,
            rho_radius=3.0,
        )


# Legacy constants for backward compatibility
THETA_P = ThresholdProfile.default().theta_P
THETA_K = ThresholdProfile.default().theta_kappa
THETA_BW = ThresholdProfile.default().theta_bw
EPSILON_TRANSPORT = ThresholdProfile.default().epsilon_transport
THETA_R = ThresholdProfile.default().theta_R
RHO_RADIUS = ThresholdProfile.default().rho_radius
THETA_BOUNDARY = ThresholdProfile.default().theta_boundary
THETA_CONTRA = ThresholdProfile.default().theta_contra
