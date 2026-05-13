"""Engine C: Guarded Hybrid Inertia — A's safety + B's adaptivity.

Blueprint §9: Manual Strata architecture with inertia-modulated
learning rate. Extracted per §17 for independent review.
"""
from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional

from engines._common import ABConfig, WeightEntry, MeasureCoordinate


class HebbianEngine_C_GuardedHybrid:
    """Candidate C: Manual Strata + Inertia-modulated learning rate.

    C keeps A's fast/slow dual-layer architecture but allows B's M_eff
    to modulate the Oja-rule learning rate within a guarded range:
      effective_eta = eta_base * clip(1.0 / M_eff_proxy, 0.5, 1.5)

    Spec §9: "C keeps A's safety, introduces B's adaptivity,
              reduces mass singularity risk, stays interpretable"
    """

    MOD_MIN = 0.5
    MOD_MAX = 1.5

    def __init__(self, config: ABConfig):
        self.config = config
        self.weights_fast: Dict[Tuple[str,str], WeightEntry] = {}
        self.weights_slow: Dict[Tuple[str,str], WeightEntry] = {}
        self.tick = 0
        self.update_count = 0
        self.exploded_count = 0
        self.fallback_count = 0
        self.p_cores_at_snapshot: List[str] = []

    def update(self, from_id, to_id, a_i, a_j, gamma,
               freeze_bonus=1.0, xin_force=0.0,
               is_external=True, xin_residual=0.0,
               z_t: Optional[MeasureCoordinate] = None):
        """A's Oja-rule on fast layer, with M_eff-modulated eta."""
        key = (from_id, to_id)
        if key not in self.weights_fast:
            self.weights_fast[key] = WeightEntry(from_id, to_id, weight=0.1)
        w = self.weights_fast[key]
        cfg = self.config

        if z_t is not None:
            w.cumulative_potential += z_t.to_phi()
        else:
            w.cumulative_potential += abs(xin_force) + abs(a_i * a_j) * 0.1
        if is_external:
            w.external_hit_count += 1
        else:
            w.internal_only_count += 1

        M_proxy = 1.0 + cfg.alpha * w.cumulative_potential
        if z_t is not None:
            M_proxy += 0.3 * (z_t.gamma_desync_cost + z_t.xin_residual_cost)
            M_proxy -= 0.2 * (z_t.cross_slice_churn_cost + z_t.magnitude_disturbance_cost)
        M_proxy = max(cfg.M_min, min(cfg.M_max, M_proxy))
        w.inertia_mass = M_proxy

        if M_proxy >= 0.95 * cfg.M_max:
            modulation = 1.0
            self.fallback_count += 1
        else:
            modulation = max(self.MOD_MIN, min(self.MOD_MAX, 1.0 / M_proxy))

        effective_eta = cfg.eta * modulation
        force = effective_eta * a_i * a_j * gamma * freeze_bonus
        decay = cfg.oja_lambda * w.weight
        delta_w = force - decay

        if abs(delta_w) > 1.0:
            delta_w = math.copysign(1.0, delta_w)
            self.exploded_count += 1

        w.last_weight_delta = delta_w
        w.weight = max(cfg.w_floor, min(cfg.w_ceil, w.weight + delta_w))
        self.update_count += 1

    def apply_global_decay(self):
        """Per-tick global decay — same as A (uniform)."""
        decay = 1.0 - self.config.decay_epsilon
        for w in self.weights_fast.values():
            w.weight = max(self.config.w_floor, w.weight * decay)

    def maybe_absorb_slow_layer(self):
        """Absorb fast -> slow at fixed intervals (same as A)."""
        self.tick += 1
        if self.tick % self.config.strata_absorb_interval == 0:
            rate = self.config.strata_absorb_rate
            for key, fast_w in self.weights_fast.items():
                if key not in self.weights_slow:
                    self.weights_slow[key] = WeightEntry(
                        fast_w.from_id, fast_w.to_id, weight=0.0, layer="slow")
                slow_w = self.weights_slow[key]
                slow_w.weight += rate * (fast_w.weight - slow_w.weight)
                slow_w.cumulative_potential = fast_w.cumulative_potential

    def get_effective_weights(self) -> Dict[Tuple[str,str], float]:
        result = {}
        all_keys = set(self.weights_fast.keys()) | set(self.weights_slow.keys())
        for key in all_keys:
            fast = self.weights_fast.get(key)
            slow = self.weights_slow.get(key)
            f_val = fast.weight if fast else 0.0
            s_val = slow.weight if slow else 0.0
            result[key] = 0.6 * f_val + 0.4 * s_val
        return result

    def snapshot_p_cores(self, p_core_ids: List[str]):
        self.p_cores_at_snapshot = list(p_core_ids)

    def get_dead_node_count(self) -> int:
        return 0

    def get_metrics(self) -> dict:
        weights = list(self.get_effective_weights().values())
        if not weights:
            return {"avg": 0, "max": 0, "min": 0, "count": 0, "entropy": 0,
                    "dead_nodes": 0, "exploded": self.exploded_count,
                    "fallback_count": self.fallback_count}
        avg_w = sum(weights) / len(weights)
        total = sum(weights) + 1e-10
        probs = [w / total for w in weights]
        entropy = -sum(p * math.log(max(p, 1e-10)) for p in probs)
        masses = [w.inertia_mass for w in self.weights_fast.values()]
        avg_mass = sum(masses) / max(len(masses), 1)
        return {
            "avg": avg_w, "max": max(weights), "min": min(weights),
            "count": len(weights), "entropy": entropy,
            "dead_nodes": 0, "exploded": self.exploded_count,
            "fallback_count": self.fallback_count,
            "avg_inertia_mass": round(avg_mass, 4),
        }
