"""Engine B: Topological Inertia — Candidate with emergent time scales.

Blueprint §4, §8: Inertia-damped Hebbian with full 7-input M_eff,
d_sigma_t internal measure time (§4.5), V_Phi velocity (§4.6),
and anomaly detection (§22). Extracted per §17.
"""
from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional

from engines._common import (
    ABConfig, WeightEntry, MeasureCoordinate, InternalMeasureTime,
)


class HebbianEngine_B_TopologicalInertia:
    """Candidate B: Inertia-damped Hebbian with emergent time scales.

    Core equation (2026.5.10.1 §4):
      ΔW_ij = (1 / M(Φ_ij)) · [η · a_i · a_j · γ · bonus - λ · W_ij]
    where:
      M(Φ) = 1 + α · Φ,  clamped to [1, M_max]

    Physical meaning:
      - New structures (shallow Φ, M ≈ 1): highly responsive
      - Old structures (deep Φ, large M): nearly immovable = "history"
    """

    def __init__(self, config: ABConfig):
        self.config = config
        self.weights: Dict[Tuple[str,str], WeightEntry] = {}
        self.tick = 0
        self.update_count = 0
        self.exploded_count = 0
        self.singularity_events = 0
        self.collapse_events = 0
        self.p_cores_at_snapshot: List[str] = []
        self.audit_buffer: List[dict] = []
        # §4.5/§4.6: d_σ_t and V_Φ tracking
        self._measure_time = InternalMeasureTime()
        self._phi_prev: float = 0.0
        self._phi_current: float = 0.0
        self._last_z_t: Optional[MeasureCoordinate] = None
        self.d_sigma_history: List[dict] = []
        # B2: V_Φ anomaly detection (§22)
        self._v_phi_window: List[float] = []
        self._v_phi_consecutive_zero: int = 0
        self.v_phi_alerts: List[dict] = []
        self.ZERO_THRESHOLD: float = 1e-5
        self.DEAD_NODE_TICKS: int = 8
        self.SPIKE_MULTIPLIER: float = 10.0

    def update(self, from_id, to_id, a_i, a_j, gamma,
               freeze_bonus=1.0, xin_force=0.0,
               is_external=True, xin_residual=0.0,
               z_t: Optional[MeasureCoordinate] = None):
        """Inertia-damped Hebbian update with full 7-input M_eff (§8.3)."""
        key = (from_id, to_id)
        if key not in self.weights:
            self.weights[key] = WeightEntry(from_id, to_id, weight=0.1)
        w = self.weights[key]
        cfg = self.config

        if is_external:
            w.external_hit_count += 1
        else:
            w.internal_only_count += 1
        w.last_xin_residual = xin_residual

        if z_t is not None:
            w.cumulative_potential += z_t.to_phi()
            self._last_z_t = z_t
        else:
            w.cumulative_potential += abs(xin_force) + abs(a_i * a_j) * 0.1

        if abs(w.last_weight_delta) < 0.05:
            w.stability_ticks += 1
        else:
            w.stability_ticks = max(0, w.stability_ticks - 2)

        # Full 7-input M_eff (§8.2-8.3)
        basin_term = cfg.alpha * w.cumulative_potential
        external_term = cfg.external_hit_weight * min(w.external_hit_count, 50)
        stability_term = 0.2 * min(w.stability_ticks, 20) / 20.0
        xin_residual_term = 0.4 * w.last_xin_residual
        total_hits = w.external_hit_count + w.internal_only_count
        internal_ratio = w.internal_only_count / max(total_hits, 1)
        self_activation_penalty = cfg.internal_only_penalty * internal_ratio

        M_phi = (1.0 + basin_term + external_term + stability_term
                 - xin_residual_term - self_activation_penalty)
        M_phi = max(cfg.M_min, min(cfg.M_max, M_phi))
        w.inertia_mass = M_phi

        singularity = M_phi >= 0.95 * cfg.M_max
        collapse = M_phi <= cfg.M_min * 1.02
        if singularity:
            self.singularity_events += 1
        if collapse and w.cumulative_potential > 1.0:
            self.collapse_events += 1

        A_t = 1.0 if is_external else 0.3
        # Phase 2.3: Strict Oja rule with inertia modulation
        # Standard Oja: ΔW = η · a_i · (a_j - W · a_i)
        # Extended:     ΔW = A_t · [η · a_i · (a_j · γ · bonus - W · a_i) - κ · xin] / M
        # The self-normalizing term (-W · a_i²) replaces manual λ·W decay,
        # mathematically guaranteeing convergence to principal component direction.
        oja_force = cfg.eta * a_i * (a_j * gamma * freeze_bonus - w.weight * a_i)
        contradiction = cfg.kappa * xin_residual
        delta_w = A_t * (oja_force - contradiction) / M_phi

        if abs(delta_w) > 1.0:
            delta_w = math.copysign(1.0, delta_w)
            self.exploded_count += 1

        w.last_weight_delta = delta_w
        w.weight = max(cfg.w_floor, min(cfg.w_ceil, w.weight + delta_w))
        self.update_count += 1

        if self.update_count % 50 == 0 or singularity or collapse:
            was_clipped = (M_phi == cfg.M_min or M_phi == cfg.M_max)
            self.audit_buffer.append({
                "from": from_id, "to": to_id,
                "phi": w.cumulative_potential, "m_eff": M_phi,
                "delta_w": delta_w, "ext_hits": w.external_hit_count,
                "int_hits": w.internal_only_count, "xin_res": xin_residual,
                "contradiction": contradiction, "a_t": A_t,
                "clipped": 1 if was_clipped else 0,
                "singularity": 1 if singularity else 0,
                "collapse": 1 if collapse else 0,
            })

    def apply_global_decay(self):
        """Per-tick inertia-protected Laplacian decay."""
        base_decay = self.config.decay_epsilon
        beta = 0.5
        if not hasattr(self, '_cached_max_phi') or self.tick % 20 == 0:
            self._cached_max_phi = max(
                (w.cumulative_potential for w in self.weights.values()), default=1.0)
            self._cached_max_phi = max(self._cached_max_phi, 0.01)
        inv_max_phi = 1.0 / self._cached_max_phi
        base_factor = base_decay * (1 + beta)
        for w in self.weights.values():
            phi_norm = w.cumulative_potential * inv_max_phi
            effective_decay = base_factor / (1 + beta * phi_norm)
            w.weight = max(self.config.w_floor, w.weight * (1.0 - effective_decay))

    def maybe_absorb_slow_layer(self):
        """No-op for engine B (no layers), but computes d_σ_t and V_Φ."""
        self.tick += 1
        self._compute_d_sigma_v_phi()

    def _compute_d_sigma_v_phi(self):
        """Compute d_σ_t (§4.5) and V_Φ(t) (§4.6) for this tick."""
        if self.weights:
            self._phi_current = sum(
                w.cumulative_potential for w in self.weights.values()
            ) / len(self.weights)
        else:
            self._phi_current = 0.0

        if self._last_z_t is not None:
            d_sigma = self._measure_time.compute_from_z(self._last_z_t)
            inputs = self._last_z_t.to_d_sigma_inputs()
        else:
            d_sigma = self._measure_time.compute(clock_delta=1.0)
            inputs = {"clock_delta": 1.0, "source_delta": 0.0,
                      "reproj_delta": 0.0, "phi_displacement": 0.0,
                      "rlis_delta": 0.0, "churn_delta": 0.0}

        epsilon = 1e-6
        phi_displacement = abs(self._phi_current - self._phi_prev)
        v_phi = phi_displacement / (epsilon + d_sigma)

        self.d_sigma_history.append({
            "tick": self.tick, "d_sigma_t": d_sigma,
            "phi_t": self._phi_current, "phi_prev": self._phi_prev,
            "v_phi": v_phi, **inputs,
        })

        # B2: V_Φ anomaly detection
        self._v_phi_window.append(v_phi)
        if len(self._v_phi_window) > 20:
            self._v_phi_window.pop(0)
        moving_avg = sum(self._v_phi_window) / len(self._v_phi_window)

        if v_phi < self.ZERO_THRESHOLD:
            self._v_phi_consecutive_zero += 1
            if self._v_phi_consecutive_zero >= self.DEAD_NODE_TICKS:
                self.v_phi_alerts.append({
                    "tick": self.tick, "alert_type": "dead_node_suspected",
                    "v_phi_current": v_phi, "v_phi_moving_avg": moving_avg,
                    "threshold": self.ZERO_THRESHOLD,
                    "consecutive_zero_ticks": self._v_phi_consecutive_zero,
                })
        else:
            self._v_phi_consecutive_zero = 0

        if len(self._v_phi_window) >= 5 and moving_avg > self.ZERO_THRESHOLD:
            if v_phi > self.SPIKE_MULTIPLIER * moving_avg:
                self.v_phi_alerts.append({
                    "tick": self.tick, "alert_type": "phase_transition_spike",
                    "v_phi_current": v_phi, "v_phi_moving_avg": moving_avg,
                    "threshold": self.SPIKE_MULTIPLIER * moving_avg,
                    "consecutive_zero_ticks": 0,
                })

        self._phi_prev = self._phi_current
        self._last_z_t = None

    def get_effective_weights(self) -> Dict[Tuple[str,str], float]:
        return {k: w.weight for k, w in self.weights.items()}

    def snapshot_p_cores(self, p_core_ids: List[str]):
        self.p_cores_at_snapshot = list(p_core_ids)

    def get_dead_node_count(self) -> int:
        threshold = 0.9 * self.config.M_max
        return sum(1 for w in self.weights.values() if w.inertia_mass > threshold)

    def get_metrics(self) -> dict:
        weights = [w.weight for w in self.weights.values()]
        if not weights:
            return {"avg": 0, "max": 0, "min": 0, "count": 0, "entropy": 0,
                    "dead_nodes": 0, "exploded": self.exploded_count,
                    "singularity_events": self.singularity_events,
                    "collapse_events": self.collapse_events}
        avg_w = sum(weights) / len(weights)
        total = sum(weights) + 1e-10
        probs = [w / total for w in weights]
        entropy = -sum(p * math.log(max(p, 1e-10)) for p in probs)
        masses = [w.inertia_mass for w in self.weights.values()]
        avg_mass = sum(masses) / len(masses)
        ext_hits = sum(w.external_hit_count for w in self.weights.values())
        int_hits = sum(w.internal_only_count for w in self.weights.values())
        d_sigma_vals = [r["d_sigma_t"] for r in self.d_sigma_history]
        v_phi_vals = [r["v_phi"] for r in self.d_sigma_history]
        d_sigma_stats = {
            "d_sigma_mean": round(sum(d_sigma_vals) / max(len(d_sigma_vals), 1), 6),
            "d_sigma_max": round(max(d_sigma_vals, default=0.0), 6),
            "v_phi_mean": round(sum(v_phi_vals) / max(len(v_phi_vals), 1), 6),
            "v_phi_max": round(max(v_phi_vals, default=0.0), 6),
            "v_phi_count": len(v_phi_vals),
        } if d_sigma_vals else {}
        return {
            "avg": avg_w, "max": max(weights), "min": min(weights),
            "count": len(weights), "entropy": entropy,
            "dead_nodes": self.get_dead_node_count(),
            "exploded": self.exploded_count,
            "singularity_events": self.singularity_events,
            "collapse_events": self.collapse_events,
            "avg_inertia_mass": round(avg_mass, 4),
            "external_hits": ext_hits, "internal_hits": int_hits,
            **d_sigma_stats,
        }
