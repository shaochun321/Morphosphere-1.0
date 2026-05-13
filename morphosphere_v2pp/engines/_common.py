"""Shared types and helpers for Hebbian A/B/C engines.

Extracted from hebbian_ab_engine.py per blueprint §17 for independent
reviewability. All data classes and utility functions live here.
"""
from __future__ import annotations
import math, json, uuid, time, copy
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

def _now(): return datetime.now(timezone.utc).isoformat()
def _jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"
def _jdump(x): return json.dumps(x, separators=(",",":"), ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# 1. Configuration
# ═══════════════════════════════════════════════════════════════

@dataclass
class ABConfig:
    """A/B test hyperparameters — aligned to blueprint Appendix A."""
    # Shared (blueprint Appendix A)
    eta: float = 0.18           # base learning rate (blueprint: 0.18)
    oja_lambda: float = 0.05    # Oja decay coefficient
    w_floor: float = 0.01       # minimum weight
    w_ceil: float = 1.0         # maximum weight

    # Engine B: Topological Inertia (blueprint §8, Appendix A)
    alpha: float = 0.5          # inertia growth coefficient
    M_max: float = 8.0          # maximum inertia mass (blueprint: 8.0)
    M_min: float = 0.5          # minimum inertia mass (blueprint: 0.5)
    decay_epsilon: float = 0.025  # global decay per tick (blueprint: 0.025)
    kappa: float = 0.15         # contradiction penalty (blueprint: 0.15)
    external_hit_weight: float = 0.4   # (blueprint: 0.4)
    internal_only_penalty: float = 0.6 # (blueprint: 0.6)

    # Engine A: Manual Strata (blueprint §7)
    strata_absorb_interval: int = 50   # slow layer absorption interval (ticks)
    strata_absorb_rate: float = 0.1    # how much of fast layer is absorbed
    prior_absorb_rate: float = 0.005   # prior layer absorption (blueprint §7.3: alpha_prior)
    prior_absorb_interval: int = 200   # prior absorbs from slow every N ticks

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class MeasureCoordinate:
    """Non-semantic measure coordinate z_t (blueprint §4.3).

    7 dimensions representing transformation costs, NOT human semantics.
    These costs are derived from process window transitions.
    """
    transition_cost: float = 0.0
    drift_cost: float = 0.0
    gamma_desync_cost: float = 0.0
    xin_residual_cost: float = 0.0
    potential_displacement_cost: float = 0.0
    cross_slice_churn_cost: float = 0.0
    magnitude_disturbance_cost: float = 0.0

    def to_phi(self) -> float:
        """Derive motion potential Φ_t from z_t (blueprint §4.4).

        Φ_t = a1*E_motion + a2*E_memory_distance + a3*E_xin_residual
             + a4*E_rlis_desync + a5*E_transition_violation + a6*E_capacity_pressure

        Uses uniform coefficients (1/6 each) as initial calibration.
        """
        return (self.transition_cost
                + self.drift_cost
                + self.gamma_desync_cost
                + self.xin_residual_cost
                + self.potential_displacement_cost
                + self.cross_slice_churn_cost
                + self.magnitude_disturbance_cost) / 7.0

    def to_d_sigma_inputs(self) -> dict:
        """Map 7-dim z_t to 6-dim d_σ_t input components (blueprint §4.5).

        The mapping is:
          clock_delta      ← 1.0 (normalized, always advances by 1 tick)
          source_delta     ← transition_cost (new source events shift time)
          reproj_delta     ← drift_cost (reprojection causes temporal offset)
          phi_displacement ← potential_displacement_cost (motion potential shift)
          rlis_delta       ← gamma_desync_cost + xin_residual_cost
          churn_delta      ← cross_slice_churn_cost + magnitude_disturbance_cost
        """
        return {
            "clock_delta": 1.0,
            "source_delta": self.transition_cost,
            "reproj_delta": self.drift_cost,
            "phi_displacement": self.potential_displacement_cost,
            "rlis_delta": self.gamma_desync_cost + self.xin_residual_cost,
            "churn_delta": self.cross_slice_churn_cost + self.magnitude_disturbance_cost,
        }

    def as_tuple(self) -> tuple:
        return (self.transition_cost, self.drift_cost,
                self.gamma_desync_cost, self.xin_residual_cost,
                self.potential_displacement_cost,
                self.cross_slice_churn_cost,
                self.magnitude_disturbance_cost)


# ═══════════════════════════════════════════════════════════════
# 1b. Internal Measure Time (blueprint §4.5)
# ═══════════════════════════════════════════════════════════════

@dataclass
class InternalMeasureTime:
    """d_σ_t — Internal measure time increment (blueprint §4.5).

    d_σ_t = c1·Δclock + c2·Δsource + c3·Δreproj + c4·ΔΦ + c5·Δrlis + c6·Δchurn

    This is NOT physical time — it is a 6-dimensional measure-theoretic
    time increment that adapts to system dynamics.

    When nothing happens (all deltas → 0), d_σ_t → c1 (clock still ticks).
    When the system is under heavy stress, d_σ_t grows → time "speeds up".
    """
    c1: float = 1.0    # normalized_clock_delta weight
    c2: float = 0.8    # source_interval_delta weight
    c3: float = 0.5    # origin_reprojection_delta weight
    c4: float = 1.2    # motion_potential_displacement weight (heaviest)
    c5: float = 0.6    # rlis_interval_delta weight
    c6: float = 0.4    # cross_slice_churn weight

    def compute(self, clock_delta: float = 1.0, source_delta: float = 0.0,
                reproj_delta: float = 0.0, phi_displacement: float = 0.0,
                rlis_delta: float = 0.0, churn_delta: float = 0.0) -> float:
        """Compute d_σ_t from 6 input deltas."""
        return (self.c1 * clock_delta
                + self.c2 * source_delta
                + self.c3 * reproj_delta
                + self.c4 * phi_displacement
                + self.c5 * rlis_delta
                + self.c6 * churn_delta)

    def compute_from_z(self, z_t: MeasureCoordinate) -> float:
        """Convenience: compute d_σ_t directly from a MeasureCoordinate."""
        inputs = z_t.to_d_sigma_inputs()
        return self.compute(**inputs)


# ═══════════════════════════════════════════════════════════════
# 2. Weight State (shared data structure)
# ═══════════════════════════════════════════════════════════════

@dataclass
class WeightEntry:
    """A single Hebbian association weight."""
    from_id: str
    to_id: str
    weight: float = 0.1
    cumulative_potential: float = 0.0   # Φ: accumulated Xin impact count
    inertia_mass: float = 1.0           # M(Φ) for engine B
    layer: str = "fast"                 # for engine A: 'fast' or 'slow'
    # v37.4.61 D1: Full M_eff tracking fields (spec §8.3)
    external_hit_count: int = 0         # repeated external data hits
    internal_only_count: int = 0        # internal-only activation count
    stability_ticks: int = 0            # consecutive ticks without large delta
    last_xin_residual: float = 0.0      # most recent Xin residual on this edge
    last_weight_delta: float = 0.0      # for stability tracking
