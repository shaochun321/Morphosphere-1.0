"""Engine A: Manual Strata — Baseline Newtonian Clock Hebbian.

Blueprint §7.2-7.3: Mechanically stratified three-layer Hebbian with
fixed absorption clocks. Extracted per §17 for independent review.
"""
from __future__ import annotations
import math
from typing import Dict, List, Tuple

from engines._common import ABConfig, WeightEntry


class HebbianEngine_A_ManualStrata:
    """Baseline A: Mechanically stratified three-layer Hebbian.

    Blueprint §7.2-7.3: fast/slow/prior strata with fixed absorption clocks.

    - Fast layer: updated every tick with standard Oja rule
    - Slow layer: absorbs fast layer every N ticks (hard clock)
    - Prior layer: absorbs slow layer every M ticks (very slow clock)

    Advantages: O(1) complexity, absolutely predictable behavior.
    Disadvantages: Deaf to burst events between absorption intervals.
    """

    def __init__(self, config: ABConfig):
        self.config = config
        self.weights_fast: Dict[Tuple[str,str], WeightEntry] = {}
        self.weights_slow: Dict[Tuple[str,str], WeightEntry] = {}
        self.weights_prior: Dict[Tuple[str,str], WeightEntry] = {}
        self.tick = 0
        self.update_count = 0
        self.exploded_count = 0
        self.p_cores_at_snapshot: List[str] = []

    def update(self, from_id, to_id, a_i, a_j, gamma,
               freeze_bonus=1.0, xin_force=0.0,
               is_external=True, xin_residual=0.0):
        """Standard Oja-rule update on fast layer."""
        key = (from_id, to_id)
        if key not in self.weights_fast:
            self.weights_fast[key] = WeightEntry(from_id, to_id, weight=0.1)
        w = self.weights_fast[key]
        cfg = self.config
        force = cfg.eta * a_i * a_j * gamma * freeze_bonus
        decay = cfg.oja_lambda * w.weight
        delta_w = force - decay
        if abs(delta_w) > 1.0:
            delta_w = math.copysign(1.0, delta_w)
            self.exploded_count += 1
        w.weight = max(cfg.w_floor, min(cfg.w_ceil, w.weight + delta_w))
        w.cumulative_potential += abs(xin_force)
        self.update_count += 1

    def apply_global_decay(self):
        """Per-tick global decay (thermodynamic erosion)."""
        decay = 1.0 - self.config.decay_epsilon
        for w in self.weights_fast.values():
            w.weight = max(self.config.w_floor, w.weight * decay)

    def maybe_absorb_slow_layer(self):
        """Absorb fast->slow and slow->prior at fixed intervals (§7.3)."""
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
        if self.tick % self.config.prior_absorb_interval == 0:
            rate = self.config.prior_absorb_rate
            for key, slow_w in self.weights_slow.items():
                if key not in self.weights_prior:
                    self.weights_prior[key] = WeightEntry(
                        slow_w.from_id, slow_w.to_id, weight=0.0, layer="prior")
                prior_w = self.weights_prior[key]
                prior_w.weight += rate * (slow_w.weight - prior_w.weight)
                prior_w.cumulative_potential = slow_w.cumulative_potential

    def get_effective_weights(self) -> Dict[Tuple[str,str], float]:
        """Return effective weights (fast + slow + prior blend)."""
        result = {}
        all_keys = (set(self.weights_fast.keys()) |
                    set(self.weights_slow.keys()) |
                    set(self.weights_prior.keys()))
        for key in all_keys:
            fast = self.weights_fast.get(key)
            slow = self.weights_slow.get(key)
            prior = self.weights_prior.get(key)
            f_val = fast.weight if fast else 0.0
            s_val = slow.weight if slow else 0.0
            p_val = prior.weight if prior else 0.0
            result[key] = 0.5 * f_val + 0.35 * s_val + 0.15 * p_val
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
                    "prior_count": 0}
        avg_w = sum(weights) / len(weights)
        total = sum(weights) + 1e-10
        probs = [w / total for w in weights]
        entropy = -sum(p * math.log(max(p, 1e-10)) for p in probs)
        prior_weights = [w.weight for w in self.weights_prior.values()]
        mean_prior = sum(prior_weights) / max(len(prior_weights), 1) if prior_weights else 0.0
        return {
            "avg": avg_w, "max": max(weights), "min": min(weights),
            "count": len(weights), "entropy": entropy,
            "dead_nodes": 0, "exploded": self.exploded_count,
            "prior_count": len(self.weights_prior),
            "mean_prior": round(mean_prior, 6),
        }
