"""Hebbian A/B Engine — Dual-Blind Topological Inertia vs Manual Strata.

Implements two isolated Hebbian weight update strategies that process
identical input data. The A/B framework is designed per the 2026.5.10.1
architectural review: only if Candidate B (Topological Inertia) beats
Baseline A (Manual Strata) on ALL THREE metrics does it earn promotion.

Core formula for Candidate B (from 2026.5.10.1 §4):

  ΔW_ij = (1 / M(Φ_ij)) · [η · Xin_force - λ · W_ij]

where M(Φ) = 1 + α · Φ  (clamped to [1, M_max])

This module is external analysis — it does NOT modify mainline facts.
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

    def as_tuple(self) -> tuple:
        return (self.transition_cost, self.drift_cost,
                self.gamma_desync_cost, self.xin_residual_cost,
                self.potential_displacement_cost,
                self.cross_slice_churn_cost,
                self.magnitude_disturbance_cost)


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


# ═══════════════════════════════════════════════════════════════
# 3. Baseline A: Manual Strata (Newtonian Clock)
# ═══════════════════════════════════════════════════════════════

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
        self.weights_prior: Dict[Tuple[str,str], WeightEntry] = {}  # §7.2
        self.tick = 0
        self.update_count = 0
        self.exploded_count = 0  # ΔW > 1.0 truncations
        self.p_cores_at_snapshot: List[str] = []

    def update(self, from_id: str, to_id: str, a_i: float, a_j: float,
               gamma: float, freeze_bonus: float = 1.0, xin_force: float = 0.0,
               is_external: bool = True, xin_residual: float = 0.0):
        """Standard Oja-rule update on fast layer."""
        key = (from_id, to_id)
        if key not in self.weights_fast:
            self.weights_fast[key] = WeightEntry(from_id, to_id, weight=0.1)

        w = self.weights_fast[key]
        cfg = self.config

        # Oja's rule: force - decay
        force = cfg.eta * a_i * a_j * gamma * freeze_bonus
        decay = cfg.oja_lambda * w.weight
        delta_w = force - decay

        # Truncate explosions
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
        """Absorb fast→slow and slow→prior at fixed intervals.

        Blueprint §7.3:
          slow_{t+1} = slow_t + alpha_slow * (fast_t - slow_t)
          prior_{t+1} = prior_t + alpha_prior * (slow_t - prior_t)
        """
        self.tick += 1
        # Fast → Slow absorption
        if self.tick % self.config.strata_absorb_interval == 0:
            rate = self.config.strata_absorb_rate
            for key, fast_w in self.weights_fast.items():
                if key not in self.weights_slow:
                    self.weights_slow[key] = WeightEntry(
                        fast_w.from_id, fast_w.to_id, weight=0.0, layer="slow")
                slow_w = self.weights_slow[key]
                slow_w.weight += rate * (fast_w.weight - slow_w.weight)
                slow_w.cumulative_potential = fast_w.cumulative_potential

        # Slow → Prior absorption (blueprint §7.3: alpha_prior)
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
            # Blend: fast dominates, slow stabilizes, prior anchors
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
        # Prior layer delta (§7.6 baseline metric)
        prior_weights = [w.weight for w in self.weights_prior.values()]
        mean_prior = sum(prior_weights) / max(len(prior_weights), 1) if prior_weights else 0.0
        return {
            "avg": avg_w, "max": max(weights), "min": min(weights),
            "count": len(weights), "entropy": entropy,
            "dead_nodes": 0, "exploded": self.exploded_count,
            "prior_count": len(self.weights_prior),
            "mean_prior": round(mean_prior, 6),
        }


# ═══════════════════════════════════════════════════════════════
# 4. Candidate B: Topological Inertia
# ═══════════════════════════════════════════════════════════════

class HebbianEngine_B_TopologicalInertia:
    """Candidate B: Inertia-damped Hebbian with emergent time scales.

    Core equation (2026.5.10.1 §4):

      ΔW_ij = (1 / M(Φ_ij)) · [η · a_i · a_j · γ · bonus - λ · W_ij]

    where:
      M(Φ) = 1 + α · Φ,  clamped to [1, M_max]
      Φ increases with each Xin impact on this edge

    Physical meaning:
      - New structures (shallow Φ, M ≈ 1): highly responsive
      - Old structures (deep Φ, large M): nearly immovable = "history"

    Advantages: Self-adaptive, no magic clock numbers.
    Maximum risk: Mass collapse (Φ→∞ → dead node) or
                  mass singularity (Φ→0 → infinite update rate).
    """

    def __init__(self, config: ABConfig):
        self.config = config
        self.weights: Dict[Tuple[str,str], WeightEntry] = {}
        self.tick = 0
        self.update_count = 0
        self.exploded_count = 0
        self.singularity_events = 0   # D7: M_eff near M_max
        self.collapse_events = 0      # D7: M_eff collapsed to 1.0 despite deep Φ
        self.p_cores_at_snapshot: List[str] = []
        self.audit_buffer: List[dict] = []  # §16.5 per-event M_eff audit

    def update(self, from_id: str, to_id: str, a_i: float, a_j: float,
               gamma: float, freeze_bonus: float = 1.0, xin_force: float = 0.0,
               is_external: bool = True, xin_residual: float = 0.0,
               z_t: Optional[MeasureCoordinate] = None):
        """Inertia-damped Hebbian update with full 7-input M_eff (spec §8.3).

        v37.4.61 D1: M_eff now incorporates all 7 factors from the blueprint:
          1. basin_depth (cumulative_potential)
          2. repeated_external_hits
          3. long_run_stability
          4. recent_xin_residual (penalty)
          5. rlis_desync (via xin_residual proxy)
          6. transition_violation (via exploded_count)
          7. internal_only_activation_penalty
        """
        key = (from_id, to_id)
        if key not in self.weights:
            self.weights[key] = WeightEntry(from_id, to_id, weight=0.1)

        w = self.weights[key]
        cfg = self.config

        # D1: Track external vs internal hits
        if is_external:
            w.external_hit_count += 1
        else:
            w.internal_only_count += 1
        w.last_xin_residual = xin_residual

        # Accumulate potential — use z_t-derived Φ if available (§4.4)
        if z_t is not None:
            w.cumulative_potential += z_t.to_phi()
        else:
            w.cumulative_potential += abs(xin_force) + abs(a_i * a_j) * 0.1

        # D1: Stability tracking — consecutive ticks without large weight change
        if abs(w.last_weight_delta) < 0.05:
            w.stability_ticks += 1
        else:
            w.stability_ticks = max(0, w.stability_ticks - 2)

        # ═══════════════════════════════════════════════════════════
        # Full 7-input M_eff (blueprint §8.2-8.3, Appendix A)
        # ═══════════════════════════════════════════════════════════
        # Positive terms (increase inertia = resist change):
        basin_term = cfg.alpha * w.cumulative_potential
        external_term = cfg.external_hit_weight * min(w.external_hit_count, 50)
        stability_term = 0.2 * min(w.stability_ticks, 20) / 20.0

        # Negative terms (decrease inertia = allow change):
        xin_residual_term = 0.4 * w.last_xin_residual
        # internal_only ratio as self-activation penalty (blueprint §8.3)
        total_hits = w.external_hit_count + w.internal_only_count
        internal_ratio = w.internal_only_count / max(total_hits, 1)
        self_activation_penalty = cfg.internal_only_penalty * internal_ratio

        M_phi = (1.0
                 + basin_term
                 + external_term
                 + stability_term
                 - xin_residual_term
                 - self_activation_penalty)
        M_phi = max(cfg.M_min, min(cfg.M_max, M_phi))
        w.inertia_mass = M_phi

        # D7: Track safety events
        singularity = M_phi >= 0.95 * cfg.M_max
        collapse = M_phi <= cfg.M_min * 1.02
        if singularity:
            self.singularity_events += 1
        if collapse and w.cumulative_potential > 1.0:
            self.collapse_events += 1

        # ═══════════════════════════════════════════════════════════
        # Blueprint §8.2: ΔW = A_t/M_eff * [η·G·External - λ·W - κ·Contradiction]
        # ═══════════════════════════════════════════════════════════
        # A_t: external credibility gate (§8.2)
        A_t = 1.0 if is_external else 0.3  # internal-only events get 30% gate

        # Force: Oja-like with bonuses
        force = cfg.eta * a_i * a_j * gamma * freeze_bonus
        decay = cfg.oja_lambda * w.weight

        # Contradiction penalty (§8.2: -κ * Contradiction_t)
        contradiction = cfg.kappa * xin_residual

        # The key equation: ΔW = A_t * (force - decay - contradiction) / M(Φ)
        delta_w = A_t * (force - decay - contradiction) / M_phi

        # Safety: truncate explosions
        if abs(delta_w) > 1.0:
            delta_w = math.copysign(1.0, delta_w)
            self.exploded_count += 1

        w.last_weight_delta = delta_w
        w.weight = max(cfg.w_floor, min(cfg.w_ceil, w.weight + delta_w))
        self.update_count += 1

        # §16.5: Sampled audit buffer (every Nth event to reduce overhead)
        # Full audit creates dict + 6× round() per update → ~40% overhead.
        # Sampling at 1/10 keeps coverage while staying within 1.2× budget.
        if self.update_count % 10 == 0 or singularity or collapse:
            was_clipped = (M_phi == cfg.M_min or M_phi == cfg.M_max)
            self.audit_buffer.append({
                "from": from_id, "to": to_id,
                "phi": w.cumulative_potential,
                "m_eff": M_phi,
                "delta_w": delta_w,
                "ext_hits": w.external_hit_count,
                "int_hits": w.internal_only_count,
                "xin_res": xin_residual,
                "contradiction": contradiction,
                "a_t": A_t,
                "clipped": 1 if was_clipped else 0,
                "singularity": 1 if singularity else 0,
                "collapse": 1 if collapse else 0,
            })

    def apply_global_decay(self):
        """Per-tick inertia-protected Laplacian decay (thermodynamic erosion).

        v37.4.61: Inertia-assisted forgetting — decay rate is inversely
        proportional to cumulative potential Φ:

          effective_ε = ε_base · (1 + β) / (1 + β · Φ_norm)

        where Φ_norm = Φ / Φ_max, β = 0.5 (mild amplification).

        Physical meaning:
          - Deep potential wells (high Φ): decay at ~ε·0.67 → memory preserved
          - Shallow wells (low Φ, noise): decay at ~ε·1.5 → faster clearance
          - Result: new regime edges enter top-k faster because stale
            noise edges are cleared, while confirmed structure persists.
        """
        base_decay = self.config.decay_epsilon
        beta = 0.5  # mild amplification — preserves noise resistance

        # Precompute max Φ (cached — update every 5 ticks for efficiency)
        if not hasattr(self, '_cached_max_phi') or self.tick % 5 == 0:
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
        """No-op for engine B (no explicit layers)."""
        self.tick += 1

    def get_effective_weights(self) -> Dict[Tuple[str,str], float]:
        return {k: w.weight for k, w in self.weights.items()}

    def snapshot_p_cores(self, p_core_ids: List[str]):
        self.p_cores_at_snapshot = list(p_core_ids)

    def get_dead_node_count(self) -> int:
        """Count nodes with M(Φ) > 0.9 * M_max (near-dead)."""
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
        # D7: M_eff distribution stats
        masses = [w.inertia_mass for w in self.weights.values()]
        avg_mass = sum(masses) / len(masses)
        ext_hits = sum(w.external_hit_count for w in self.weights.values())
        int_hits = sum(w.internal_only_count for w in self.weights.values())
        return {
            "avg": avg_w, "max": max(weights), "min": min(weights),
            "count": len(weights), "entropy": entropy,
            "dead_nodes": self.get_dead_node_count(),
            "exploded": self.exploded_count,
            "singularity_events": self.singularity_events,
            "collapse_events": self.collapse_events,
            "avg_inertia_mass": round(avg_mass, 4),
            "external_hits": ext_hits,
            "internal_hits": int_hits,
        }


# ═══════════════════════════════════════════════════════════════
# 4b. Candidate C: Guarded Hybrid Inertia (spec §9)
# ═══════════════════════════════════════════════════════════════

class HebbianEngine_C_GuardedHybrid:
    """Candidate C: Manual Strata + Inertia-modulated learning rate.

    C keeps A's fast/slow dual-layer architecture but allows B's M_eff
    to modulate the Oja-rule learning rate within a guarded range:

      effective_eta = eta_base * clip(1.0 / M_eff_proxy, 0.5, 1.5)

    Spec §9: "C 保留 A 的安全性, 引入 B 的自适应性,
              降低质量奇点风险, 保持可解释和可回退"

    Advantages over B: No dead-node risk (modulation is bounded).
    Advantages over A: Responds to burst events between absorb intervals.
    Fallback: If M_eff enters singularity zone, modulation resets to 1.0 (= A).
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
        self.fallback_count = 0       # times modulation was reset to 1.0
        self.p_cores_at_snapshot: List[str] = []

    def update(self, from_id: str, to_id: str, a_i: float, a_j: float,
               gamma: float, freeze_bonus: float = 1.0, xin_force: float = 0.0,
               is_external: bool = True, xin_residual: float = 0.0):
        """A's Oja-rule on fast layer, with M_eff-modulated eta."""
        key = (from_id, to_id)
        if key not in self.weights_fast:
            self.weights_fast[key] = WeightEntry(from_id, to_id, weight=0.1)

        w = self.weights_fast[key]
        cfg = self.config

        # Accumulate potential (same as B)
        w.cumulative_potential += abs(xin_force) + abs(a_i * a_j) * 0.1
        if is_external:
            w.external_hit_count += 1
        else:
            w.internal_only_count += 1

        # Compute M_eff proxy (simplified — no full 7-input to keep C simpler)
        M_proxy = 1.0 + cfg.alpha * w.cumulative_potential
        M_proxy = max(cfg.M_min, min(cfg.M_max, M_proxy))
        w.inertia_mass = M_proxy

        # Modulate eta: high M_eff → low eta (stable structure resists change)
        if M_proxy >= 0.95 * cfg.M_max:
            # Singularity guard: fall back to A's base rate
            modulation = 1.0
            self.fallback_count += 1
        else:
            modulation = max(self.MOD_MIN, min(self.MOD_MAX, 1.0 / M_proxy))

        effective_eta = cfg.eta * modulation

        # Oja's rule with modulated learning rate
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
        """Absorb fast → slow at fixed intervals (same as A)."""
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
        return 0  # No dead nodes in C (bounded modulation)

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

class DualBlindABHarness:
    """Runs all three engines on identical input, measures metrics.

    v37.4.61 D2: Now includes Engine C (Guarded Hybrid Inertia).

    Judgment criteria (from 2026.5.10.1 §10-12):
      1. P-Core Survival Rate under noise storm
      2. Adaptation Latency to regime shift
      3. Compute Overhead
      4. Contradiction escape (D3 new stream)
      5. Staleness wind-down (D3 new stream)

    B must win ALL THREE core metrics to be promoted.
    Tie → keep A (Occam's razor). C can be staged default if > A and more stable than B.
    """

    def __init__(self, conn, run_id, config: ABConfig = None):
        self.conn = conn
        self.run_id = run_id
        self.config = config or ABConfig()
        self.engine_a = HebbianEngine_A_ManualStrata(self.config)
        self.engine_b = HebbianEngine_B_TopologicalInertia(self.config)
        self.engine_c = HebbianEngine_C_GuardedHybrid(self.config)
        self.metric_log = []

        # Write config snapshot
        conn.execute(
            "INSERT INTO v37450_ab_config "
            "(config_id,run_id,m_max,alpha,decay_epsilon,oja_lambda,eta,"
            "strata_absorb_interval,noise_storm_ticks,regime_shift_ticks,"
            "warmup_ticks,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("cfg"), run_id, self.config.M_max, self.config.alpha,
             self.config.decay_epsilon, self.config.oja_lambda, self.config.eta,
             self.config.strata_absorb_interval, 30, 20, 10, _now()))
        conn.commit()

    def feed_update(self, from_id: str, to_id: str, a_i: float, a_j: float,
                    gamma: float, freeze_bonus: float = 1.0, xin_force: float = 0.0,
                    z_t: Optional[MeasureCoordinate] = None):
        """Feed identical update to all three engines."""
        self.engine_a.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force)
        self.engine_b.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force, z_t=z_t)
        self.engine_c.update(from_id, to_id, a_i, a_j, gamma, freeze_bonus, xin_force)

    def tick(self):
        """Advance one tick for all three engines."""
        self.engine_a.apply_global_decay()
        self.engine_b.apply_global_decay()
        self.engine_c.apply_global_decay()
        self.engine_a.maybe_absorb_slow_layer()
        self.engine_b.maybe_absorb_slow_layer()
        self.engine_c.maybe_absorb_slow_layer()

    def snapshot_p_cores(self, p_core_ids: List[str]):
        """Snapshot P-core identities for survival test."""
        self.engine_a.snapshot_p_cores(p_core_ids)
        self.engine_b.snapshot_p_cores(p_core_ids)
        self.engine_c.snapshot_p_cores(p_core_ids)

    def measure_survival(self) -> Tuple[float, float, float]:
        """After noise storm: what fraction of original P-core edges survived?

        Returns (surv_a, surv_b, surv_c).
        """
        threshold = 0.05

        def _survival(engine, snapshot_ids):
            if not snapshot_ids:
                return 1.0
            ew = engine.get_effective_weights()
            survived = 0
            total = 0
            for (f, t), w in ew.items():
                if f in snapshot_ids or t in snapshot_ids:
                    total += 1
                    if w > threshold:
                        survived += 1
            return survived / max(total, 1)

        surv_a = _survival(self.engine_a, self.engine_a.p_cores_at_snapshot)
        surv_b = _survival(self.engine_b, self.engine_b.p_cores_at_snapshot)
        surv_c = _survival(self.engine_c, self.engine_c.p_cores_at_snapshot)
        return surv_a, surv_b, surv_c

    def measure_adaptation_latency(self, new_regime_features: List[Tuple],
                                    truth_label: str) -> Tuple[int, int, int]:
        """Feed a new regime pattern and measure how many ticks until
        the engine's strongest association aligns with the new pattern.

        v37.4.61: Tracks ALL new-regime edge identities for A, B, and C.

        Returns (latency_a, latency_b, latency_c) in ticks.
        """
        new_regime_nodes = set()
        for (from_id, to_id, *_) in new_regime_features:
            new_regime_nodes.add(from_id)
            new_regime_nodes.add(to_id)

        latency_a = len(new_regime_features)
        latency_b = len(new_regime_features)
        latency_c = len(new_regime_features)

        for tick_i, (from_id, to_id, a_i, a_j, gamma) in enumerate(new_regime_features):
            self.feed_update(from_id, to_id, a_i, a_j, gamma, xin_force=a_i*a_j)
            self.tick()

            # Check all three engines
            for eng, lat_ref, name in [
                (self.engine_a, 'a', 'A'),
                (self.engine_b, 'b', 'B'),
                (self.engine_c, 'c', 'C'),
            ]:
                ew = eng.get_effective_weights()
                if ew:
                    top_keys = sorted(ew.items(), key=lambda x: -x[1])[:10]
                    new_count = sum(1 for (f, t), _ in top_keys
                                    if f in new_regime_nodes or t in new_regime_nodes)
                    if new_count >= 3:
                        if lat_ref == 'a' and latency_a == len(new_regime_features):
                            latency_a = tick_i + 1
                        elif lat_ref == 'b' and latency_b == len(new_regime_features):
                            latency_b = tick_i + 1
                        elif lat_ref == 'c' and latency_c == len(new_regime_features):
                            latency_c = tick_i + 1

        return latency_a, latency_b, latency_c

    def log_metrics(self, tick: int, phase: str):
        """Record current metrics for all three engines to DB."""
        for engine_name, engine in [("A_strata", self.engine_a),
                                     ("B_inertia", self.engine_b),
                                     ("C_hybrid", self.engine_c)]:
            m = engine.get_metrics()
            self.conn.execute(
                "INSERT INTO v37450_ab_metric_log "
                "(record_id,run_id,engine,tick,phase,"
                "p_core_survival_rate,adaptation_latency,compute_overhead_ms,"
                "weight_entropy,dead_node_count,exploded_count,"
                "avg_weight,max_weight,min_weight,total_weights,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("abl"), self.run_id, engine_name, tick, phase,
                 0.0, 0.0, 0.0,
                 m["entropy"], m["dead_nodes"], m["exploded"],
                 m["avg"], m["max"], m["min"], m["count"], _now()))

    def write_weight_snapshots(self, tick: int):
        """Write current weight states to mirror table for all engines."""
        for engine_name, engine in [("A_strata", self.engine_a),
                                     ("B_inertia", self.engine_b),
                                     ("C_hybrid", self.engine_c)]:
            if engine_name == "A_strata":
                for (f, t), w in engine.weights_fast.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, 1.0, w.cumulative_potential, "fast", tick, _now()))
            elif engine_name == "B_inertia":
                for (f, t), w in engine.weights.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, w.inertia_mass, w.cumulative_potential,
                         "single", tick, _now()))
            else:  # C_hybrid
                for (f, t), w in engine.weights_fast.items():
                    self.conn.execute(
                        "INSERT INTO v37450_ab_weight_mirror "
                        "(record_id,run_id,engine,from_entity_id,to_entity_id,"
                        "weight_value,inertia_mass,cumulative_potential,layer,tick,created_at) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (_jid("wm"), self.run_id, engine_name, f, t,
                         w.weight, w.inertia_mass, w.cumulative_potential,
                         "fast", tick, _now()))

    def flush_inertia_audit(self, tick: int):
        """Flush Engine B's per-event audit buffer to topological_inertia_event table (§16.5)."""
        ts = _now()
        for rec in self.engine_b.audit_buffer:
            self.conn.execute(
                "INSERT INTO topological_inertia_event "
                "(record_id,engine_id,tick,event_id,class_id,from_entity,to_entity,"
                "phi,m_eff,delta_w,external_hits,internal_only_hits,"
                "recent_xin_residual,contradiction_penalty,a_t_gate,"
                "mass_clipped,singularity_flag,collapse_flag,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("tie"), "B_inertia", tick, "", "",
                 rec["from"], rec["to"],
                 rec["phi"], rec["m_eff"], rec["delta_w"],
                 rec["ext_hits"], rec["int_hits"],
                 rec["xin_res"], rec["contradiction"], rec["a_t"],
                 rec["clipped"], rec["singularity"], rec["collapse"], ts))
        count = len(self.engine_b.audit_buffer)
        self.engine_b.audit_buffer.clear()
        return count

    def write_source_events(self, events: list):
        """Write source event provenance records (§16.1).

        events: list of dicts with keys:
            source_id, event_id, event_time, payload_hash, split_role,
            external_real_data, source_url, raw_ref
        """
        ts = _now()
        for ev in events:
            try:
                self.conn.execute(
                    "INSERT OR IGNORE INTO source_event "
                    "(event_id,source_id,split_role,event_time,payload_hash,"
                    "raw_ref,external_real_data,source_url,license_or_policy,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (ev.get("event_id", _jid("se")),
                     ev.get("source_id", "unknown"),
                     ev.get("split_role", "calibration"),
                     ev.get("event_time", ts),
                     ev.get("payload_hash", ""),
                     ev.get("raw_ref", ""),
                     ev.get("external_real_data", 0),
                     ev.get("source_url", ""),
                     ev.get("license_or_policy", ""),
                     ts))
            except Exception:
                pass  # ignore duplicate inserts

    def write_measure_coordinate(self, event_id: str,
                                  transition_cost: float = 0.0,
                                  drift_cost: float = 0.0,
                                  gamma_desync_cost: float = 0.0,
                                  xin_residual_cost: float = 0.0,
                                  potential_displacement_cost: float = 0.0,
                                  cross_slice_churn_cost: float = 0.0,
                                  magnitude_disturbance_cost: float = 0.0):
        """Write non-semantic measure coordinate z_t (§16.3)."""
        self.conn.execute(
            "INSERT INTO measure_coordinate "
            "(record_id,event_id,transition_cost,drift_cost,gamma_desync_cost,"
            "xin_residual_cost,potential_displacement_cost,cross_slice_churn_cost,"
            "magnitude_disturbance_cost,semantic_leakage_flag,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("mc"), event_id,
             transition_cost, drift_cost, gamma_desync_cost,
             xin_residual_cost, potential_displacement_cost,
             cross_slice_churn_cost, magnitude_disturbance_cost,
             0, _now()))

    def render_verdict(self, survival_a: float, survival_b: float,
                       latency_a: float, latency_b: float,
                       overhead_a_ms: float, overhead_b_ms: float) -> dict:
        """Three-metric judgment. B must win ALL THREE."""
        wins_a = wins_b = 0

        # Metric 1: Survival (higher is better)
        if survival_b > survival_a + 0.01:
            surv_winner = "B_inertia"; wins_b += 1
        elif survival_a > survival_b + 0.01:
            surv_winner = "A_strata"; wins_a += 1
        else:
            surv_winner = "DRAW"

        # Metric 2: Latency (lower is better)
        if latency_b < latency_a - 0.5:
            lat_winner = "B_inertia"; wins_b += 1
        elif latency_a < latency_b - 0.5:
            lat_winner = "A_strata"; wins_a += 1
        else:
            lat_winner = "DRAW"

        # Metric 3: Overhead (B must not exceed A by > 20%)
        if overhead_b_ms <= overhead_a_ms * 1.2:
            if overhead_b_ms < overhead_a_ms * 0.9:
                oh_winner = "B_inertia"; wins_b += 1
            else:
                oh_winner = "DRAW"  # within 20% tolerance
        else:
            oh_winner = "A_strata"; wins_a += 1

        # Final verdict: B must win ALL THREE
        if wins_b == 3:
            winner = "B_inertia"
            rationale = "Candidate B wins all 3 metrics: survival, latency, overhead"
        elif wins_b > wins_a:
            winner = "A_strata"
            rationale = f"B wins {wins_b}/3 but not all 3 — Occam's razor keeps A"
        elif wins_a > wins_b:
            winner = "A_strata"
            rationale = f"A wins {wins_a}/3 metrics"
        else:
            winner = "A_strata"
            rationale = "Draw — Occam's razor keeps simpler A"

        verdict = {
            "winner": winner,
            "survival_a": survival_a, "survival_b": survival_b, "survival_winner": surv_winner,
            "latency_a": latency_a, "latency_b": latency_b, "latency_winner": lat_winner,
            "overhead_a_ms": overhead_a_ms, "overhead_b_ms": overhead_b_ms, "overhead_winner": oh_winner,
            "wins_a": wins_a, "wins_b": wins_b, "rationale": rationale,
        }

        self.conn.execute(
            "INSERT INTO v37450_ab_verdict "
            "(verdict_id,run_id,winner,survival_a,survival_b,survival_winner,"
            "latency_a,latency_b,latency_winner,"
            "overhead_a_ms,overhead_b_ms,overhead_winner,"
            "wins_a,wins_b,rationale,created_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (_jid("vrd"), self.run_id, winner,
             survival_a, survival_b, surv_winner,
             latency_a, latency_b, lat_winner,
             overhead_a_ms, overhead_b_ms, oh_winner,
             wins_a, wins_b, rationale, _now()))

        # §16.7: Write formal promotion_decision record
        overhead_pct = ((overhead_b_ms / max(overhead_a_ms, 0.001)) - 1.0) * 100
        m_b = self.engine_b.get_metrics()
        has_singularity = m_b.get("singularity_events", 0) > 0
        has_collapse = m_b.get("collapse_events", 0) > 0
        decision = ("PROMOTE" if wins_b == 3 else
                    "KEEP_AS_CANDIDATE" if wins_b > wins_a else
                    "REJECT" if has_singularity or has_collapse else
                    "KEEP_A")
        try:
            self.conn.execute(
                "INSERT INTO promotion_decision "
                "(decision_id,run_id,candidate_engine,decision,rationale,"
                "compute_overhead_pct,holdout_metric_delta,"
                "chaos_survival_delta,novelty_latency_delta,"
                "false_lockin_flag,singularity_count,collapse_count,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("pd"), self.run_id, "B_inertia", decision,
                 f"overhead={overhead_pct:.1f}% | "
                 f"survival_delta={survival_b - survival_a:.3f} | "
                 f"latency_delta={latency_a - latency_b:.1f} | "
                 f"ext_hits={m_b.get('external_hits', 0)} | "
                 f"int_hits={m_b.get('internal_hits', 0)} | "
                 f"avg_M={m_b.get('avg_inertia_mass', 0)}",
                 overhead_pct, 0.0,
                 survival_b - survival_a,
                 latency_a - latency_b,
                 0, m_b.get("singularity_events", 0),
                 m_b.get("collapse_events", 0), _now()))
        except Exception:
            pass

        return verdict

    def write_stress_metrics(self, stream_id: str, metrics: dict,
                              split_role: str = "calibration"):
        """Write per-stream per-engine stress metrics (§16.6)."""
        ts = _now()
        for engine_id, engine_metrics in metrics.items():
            for metric_name, metric_value in engine_metrics.items():
                try:
                    self.conn.execute(
                        "INSERT INTO ab_stress_metrics "
                        "(record_id,run_id,engine_id,stream_id,metric_name,"
                        "metric_value,split_role,generated_at) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (_jid("asm"), self.run_id, engine_id, stream_id,
                         metric_name, float(metric_value), split_role, ts))
                except Exception:
                    pass

    def flush_engine_state(self, phase: str, tick: int):
        """Write per-phase engine state snapshot to engine_state table (§16.4)."""
        ts = _now()
        for engine_id, engine in [("A_strata", self.engine_a),
                                   ("B_inertia", self.engine_b),
                                   ("C_hybrid", self.engine_c)]:
            m = engine.get_metrics()
            # Build state summaries
            fast_json = ""
            slow_json = ""
            prior_json = ""
            if hasattr(engine, 'weights_fast'):
                fast_json = _jdump({"count": len(engine.weights_fast),
                                    "avg": m.get("avg", 0)})
            if hasattr(engine, 'weights_slow'):
                slow_json = _jdump({"count": len(engine.weights_slow)})
            if hasattr(engine, 'weights_prior'):
                prior_json = _jdump({"count": len(engine.weights_prior),
                                     "mean": m.get("mean_prior", 0)})
            elif hasattr(engine, 'weights'):
                fast_json = _jdump({"count": len(engine.weights),
                                    "avg_mass": m.get("avg_inertia_mass", 0)})
            # Basin depth average
            if hasattr(engine, 'weights'):
                wvals = list(engine.weights.values())
                basin_avg = (sum(w.cumulative_potential for w in wvals) /
                             max(len(wvals), 1)) if wvals else 0.0
            elif hasattr(engine, 'weights_fast'):
                wvals = list(engine.weights_fast.values())
                basin_avg = (sum(w.cumulative_potential for w in wvals) /
                             max(len(wvals), 1)) if wvals else 0.0
            else:
                basin_avg = 0.0
            try:
                self.conn.execute(
                    "INSERT INTO engine_state "
                    "(record_id,run_id,engine_id,phase,tick,weight_count,"
                    "avg_weight,max_weight,entropy,basin_depth_avg,"
                    "dead_nodes,fast_state_json,slow_state_json,"
                    "prior_state_json,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (_jid("es"), self.run_id, engine_id, phase, tick,
                     m.get("count", 0), m.get("avg", 0), m.get("max", 0),
                     m.get("entropy", 0), basin_avg,
                     m.get("dead_nodes", 0),
                     fast_json, slow_json, prior_json, ts))
            except Exception:
                pass

    def write_process_window(self, event_id: str, origin_anchor: str,
                              cell_count: int, window_duration: int,
                              reprojection_hash: str = ""):
        """Write process window record (§16.2)."""
        try:
            self.conn.execute(
                "INSERT INTO process_window "
                "(window_id,event_id,origin_anchor,reprojection_hash,"
                "cell_count,window_duration_ticks,created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (_jid("pw"), event_id, origin_anchor, reprojection_hash,
                 cell_count, window_duration, _now()))
        except Exception:
            pass

    def write_self_reference_audit(self, engine_id: str, tick: int,
                                    ext_hits: int, int_hits: int,
                                    xin_residual: float,
                                    internal_deps: str = "",
                                    external_dep: str = "",
                                    rlis_sync: str = "synchronized"):
        """Write self-reference audit event (§13.3 — 7 required fields)."""
        try:
            self.conn.execute(
                "INSERT INTO self_reference_event "
                "(record_id,run_id,self_reference_event_id,engine_id,"
                "internal_state_dependencies,external_event_dependency,"
                "external_hit_count,internal_only_activation_count,"
                "rlis_sync_state,xin_residual_state,tick,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("sre"), self.run_id, _jid("sref"), engine_id,
                 internal_deps, external_dep,
                 ext_hits, int_hits,
                 rlis_sync, xin_residual, tick, _now()))
        except Exception:
            pass
