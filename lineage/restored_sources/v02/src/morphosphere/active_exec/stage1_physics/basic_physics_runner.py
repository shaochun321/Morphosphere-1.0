"""Minimal diagnostic physical signal generator for v8.5.3 physical-freeze.

This module intentionally remains small and deterministic. It is not a final
biophysical model and must not be used for scientific conclusions. Its job is to
replace the single smooth diagnostic event channel with heterogeneous,
non-smooth, noisy, multi-variable signals while keeping the existing SPMS schema
and governance interfaces frozen.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from typing import Iterable


def sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return ex / (1.0 + ex)


@dataclass(frozen=True)
class BasicPhysicsSignal:
    """Signal row ready for information_fiber insertion."""

    V_mean: float
    V_slope: float
    release_proxy: float
    afferent_current: float
    spike_rate: float
    spike_regularity: float
    timing_precision: float
    adaptation_state: float
    signal_uncertainty: float
    source_signal_refs: dict[str, object]
    provenance_hash: str


class BasicPhysicsRunner:
    """Heterogeneous diagnostic physical driver.

    Contract:
    - Inputs: clock step, cell index, dt, and optional geometry coordinates.
    - Output: BasicPhysicsSignal values for information_fiber.
    - Constraints: per-cell amplitude/frequency/phase/threshold/gain variation,
      deterministic pseudo-noise, non-zero spike rates for a subset of rows, and
      no schema changes.
    """

    profile_id = "basic_physics_v1"

    def __init__(self, cell_count: int, dt: float = 0.01, seed: int = 8531) -> None:
        self.cell_count = int(cell_count)
        self.dt = float(dt)
        self.seed = int(seed)
        self._prev_v = [-66.0 + 0.03 * (i % 11) for i in range(self.cell_count)]
        self._amp = [0.55 + 0.015 * (i % 13) + 0.04 * math.sin(i * 0.31) for i in range(self.cell_count)]
        self._omega = [16.0 + 0.9 * (i % 7) + 0.25 * math.cos(i * 0.17) for i in range(self.cell_count)]
        self._phase = [self._phase_for_cell(i) for i in range(self.cell_count)]
        self._threshold = [-0.08 + 0.018 * (i % 9) for i in range(self.cell_count)]
        self._gain = [0.19 + 0.012 * (i % 5) for i in range(self.cell_count)]
        self._tau = [0.018 + 0.0015 * (i % 6) for i in range(self.cell_count)]
        self._base_release = [0.95 + 0.05 * ((i % 10) / 9.0) for i in range(self.cell_count)]

    def _phase_for_cell(self, cell_index: int) -> float:
        raw = hashlib.sha256(f"{self.seed}:phase:{cell_index}".encode("utf-8")).digest()
        u = int.from_bytes(raw[:8], "big") / float(2**64 - 1)
        return 2.0 * math.pi * u

    def _noise(self, clock_n: int, cell_index: int) -> float:
        # Deterministic local RNG so repeated runs reproduce exactly while the
        # generated signal still has non-smooth noise at each clock/cell point.
        rng = random.Random(self.seed + 1009 * int(clock_n) + 9176 * int(cell_index))
        return rng.gauss(0.0, 1.0)

    def step_cell(
        self,
        clock_n: int,
        cell_index: int,
        position: Iterable[float] | None = None,
    ) -> BasicPhysicsSignal:
        i = int(cell_index)
        t = int(clock_n) * self.dt
        x, y, z = (0.0, 0.0, 0.0)
        if position is not None:
            vals = list(position)
            if len(vals) >= 3:
                x, y, z = float(vals[0]), float(vals[1]), float(vals[2])
        geom_term = 0.03 * math.sin(0.21 * x + 0.17 * y + 0.11 * z)
        stimulus = self._amp[i] * math.sin(self._omega[i] * t + self._phase[i])
        stimulus += 0.10 * self._noise(clock_n, i)
        stimulus += geom_term

        met_open = sigmoid((stimulus - self._threshold[i]) / self._gain[i])
        v_target = -68.0 + 34.0 * met_open + 0.8 * geom_term
        prev_v = self._prev_v[i]
        alpha = min(1.0, self.dt / max(self._tau[i], 1e-9))
        V_hair = prev_v + alpha * (v_target - prev_v)
        V_slope = (V_hair - prev_v) / max(self.dt, 1e-12)
        self._prev_v[i] = V_hair

        release = self._base_release[i] * sigmoid((V_hair + 50.0) / 5.0)
        V_aff = -70.0 + 30.0 * release
        spike_rate = max(0.0, 50.0 * (V_aff + 60.0) / 10.0)
        spike_regularity = 1.0 / (1.0 + abs(spike_rate - 18.0) / 30.0)
        timing_precision = 0.006 + 0.0004 * (i % 11) + 0.00005 * (clock_n % 5)
        adaptation_state = max(0.0, min(1.0, 0.42 + 0.35 * met_open + 0.08 * math.sin(0.37 * clock_n + 0.13 * i)))
        uncertainty = 0.018 + 0.004 * abs(self._noise(clock_n + 77, i))
        refs = {
            "profile_id": self.profile_id,
            "clock_n": int(clock_n),
            "node_id": i,
            "driver": "sinusoidal_heterogeneous_noise_met_gate_first_order_membrane",
            "seed": self.seed,
        }
        phash = hashlib.sha256(
            f"{self.profile_id}:{self.seed}:{clock_n}:{i}:{V_hair:.12f}:{spike_rate:.12f}".encode("utf-8")
        ).hexdigest()[:24]
        return BasicPhysicsSignal(
            V_mean=float(V_hair),
            V_slope=float(V_slope),
            release_proxy=float(release),
            afferent_current=float(V_aff),
            spike_rate=float(spike_rate),
            spike_regularity=float(spike_regularity),
            timing_precision=float(timing_precision),
            adaptation_state=float(adaptation_state),
            signal_uncertainty=float(uncertainty),
            source_signal_refs=refs,
            provenance_hash=f"bpv1_{phash}",
        )
