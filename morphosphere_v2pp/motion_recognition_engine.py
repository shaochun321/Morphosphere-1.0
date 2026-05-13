"""Motion Process Generator & State Recognition Module.

Creates structured motion regimes at the bottom layer and tests whether
the upper-layer memory system (FHPMS + Hebbian + transport) can:
1. Distinguish different motion states (stationary, drift, oscillation, jump)
2. Store motion relationships efficiently via Hebbian associations
3. Evolve from async recognition (delayed) toward sync recognition (predictive)

This is the core experiment module: motion_recognition_engine.py
"""
from __future__ import annotations
import math, random, json, uuid, sqlite3, time
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

def _now(): return datetime.now(timezone.utc).isoformat()
def _jid(p): return f"{p}_{uuid.uuid4().hex[:8]}"

# ═══════════════════════════════════════════════════════════════
# 1. Motion Regimes: Bottom-Layer Process Generator
# ═══════════════════════════════════════════════════════════════

MOTION_REGIMES = {
    "stationary":  {"velocity": 0.0,   "noise": 0.02, "period": 0,   "jump_prob": 0.0},
    "slow_drift":  {"velocity": 0.05,  "noise": 0.03, "period": 0,   "jump_prob": 0.0},
    "fast_drift":  {"velocity": 0.2,   "noise": 0.05, "period": 0,   "jump_prob": 0.0},
    "oscillation": {"velocity": 0.0,   "noise": 0.02, "period": 8,   "jump_prob": 0.0},
    "jump":        {"velocity": 0.0,   "noise": 0.02, "period": 0,   "jump_prob": 0.3},
    "diffusion":   {"velocity": 0.0,   "noise": 0.15, "period": 0,   "jump_prob": 0.0},
    # Phase 3.1: Neural signal regimes (for calcium imaging / ephys data)
    "burst_firing":    {"velocity": 0.0, "noise": 0.01, "period": 0, "jump_prob": 0.0,
                        "signal_burst": True, "signal_variance": 0.8},
    "sustained_activity": {"velocity": 0.0, "noise": 0.01, "period": 0, "jump_prob": 0.0,
                           "signal_sustained": True, "signal_variance": 0.3},
}

@dataclass
class MotionState:
    regime: str
    window_k: int
    x: float; y: float; z: float
    vx: float; vy: float; vz: float
    displacement: float
    angular_velocity: float

class MotionProcessGenerator:
    """Generate a long-window motion process with regime transitions."""

    def __init__(self, total_windows=60, n_cells=40, seed=42):
        self.total_windows = total_windows
        self.n_cells = n_cells
        self.rng = random.Random(seed)
        # Schedule: which regime at which window
        self.schedule = self._build_schedule()
        # Cell positions: [cell_id] -> (x, y, z)
        self.positions = {i: (self.rng.gauss(0, 1), self.rng.gauss(0, 1),
                              self.rng.gauss(0, 0.5)) for i in range(n_cells)}
        self.velocities = {i: (0.0, 0.0, 0.0) for i in range(n_cells)}
        self.history = []  # list of MotionState per window

    def _build_schedule(self):
        """Create a regime schedule with transitions."""
        schedule = []
        regimes = ["stationary", "slow_drift", "oscillation", "fast_drift",
                    "stationary", "jump", "diffusion", "slow_drift",
                    "oscillation", "stationary"]
        seg_len = max(1, self.total_windows // len(regimes))
        for i, regime in enumerate(regimes):
            for k in range(seg_len):
                if len(schedule) < self.total_windows:
                    schedule.append(regime)
        while len(schedule) < self.total_windows:
            schedule.append("stationary")
        return schedule

    def step(self, k):
        """Advance one window, return (regime, positions, displacements)."""
        regime = self.schedule[min(k, len(self.schedule)-1)]
        params = MOTION_REGIMES[regime]

        displacements = {}
        for i in range(self.n_cells):
            x, y, z = self.positions[i]
            vx, vy, vz = self.velocities[i]

            # Drift
            dx = params["velocity"] * (1 + 0.3 * self.rng.gauss(0, 1))
            dy = params["velocity"] * 0.5 * self.rng.gauss(0, 1)
            dz = params["velocity"] * 0.2 * self.rng.gauss(0, 1)

            # Oscillation
            if params["period"] > 0:
                phase = 2 * math.pi * k / params["period"]
                dx += 0.3 * math.sin(phase + i * 0.1)
                dy += 0.2 * math.cos(phase + i * 0.1)

            # Jump
            if self.rng.random() < params["jump_prob"]:
                dx += self.rng.gauss(0, 2.0)
                dy += self.rng.gauss(0, 2.0)

            # Noise
            dx += self.rng.gauss(0, params["noise"])
            dy += self.rng.gauss(0, params["noise"])
            dz += self.rng.gauss(0, params["noise"] * 0.3)

            x += dx; y += dy; z += dz
            self.positions[i] = (x, y, z)
            self.velocities[i] = (dx, dy, dz)
            displacements[i] = math.sqrt(dx**2 + dy**2 + dz**2)

        avg_disp = sum(displacements.values()) / self.n_cells
        avg_vx = sum(self.velocities[i][0] for i in range(self.n_cells)) / self.n_cells
        avg_vy = sum(self.velocities[i][1] for i in range(self.n_cells)) / self.n_cells
        angular = math.atan2(avg_vy, avg_vx) if (abs(avg_vx) + abs(avg_vy)) > 0.01 else 0

        state = MotionState(
            regime=regime, window_k=k,
            x=sum(p[0] for p in self.positions.values()) / self.n_cells,
            y=sum(p[1] for p in self.positions.values()) / self.n_cells,
            z=sum(p[2] for p in self.positions.values()) / self.n_cells,
            vx=avg_vx, vy=avg_vy, vz=0,
            displacement=avg_disp, angular_velocity=angular)
        self.history.append(state)
        return state, dict(self.positions), displacements


# ═══════════════════════════════════════════════════════════════
# 2. Feature Extractor (shared by all recognizers)
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = ["disp_mean", "disp_std", "coherence", "periodicity",
                 "jump_score", "freq_energy", "accel", "vel_consistency"]

class HebbianSignalTransform:
    """Mediates the transform: raw signal → spacetime measure → motion proxy.

    Architecture (per 2026.5.14 review):
      The Morphosphere's canonical notion of "motion" lives in the
      spacetime measure d_σ_t and motion potential V_Φ(t), NOT in raw
      signal variance. When processing calcium imaging data (where
      spatial displacement ≡ 0), we must map:

        ΔF/F signals → MeasureCoordinate z_t → Φ(t) → d_σ_t → displacement proxy

      This mapping is NOT a fixed formula but is mediated by a set of
      Hebbian weights that are trained (fixed) during calibration and
      then frozen for inference. The weights form a hypergraph connecting
      signal-space features to the 7-dimensional z_t cost space.

    The transform:
      1. Signal features (mean, std, peak rate, variance, ...) are computed
         per window from the raw ΔF/F traces.
      2. These are mapped to z_t via W_signal (6×7 Hebbian weight matrix):
           z_t[j] = Σ_i W_signal[i][j] · signal_feature[i]
      3. Φ(t) = z_t.to_phi()  (canonical motion potential)
      4. d_σ_t = InternalMeasureTime.compute_from_z(z_t)  (spacetime measure)
      5. The displacement proxy used by FeatureExtractor is d_σ_t, NOT raw variance.
    """

    # Signal feature names (input dimension = 6)
    SIGNAL_FEATURES = [
        "sig_mean",        # mean ΔF/F across cells
        "sig_std",         # std ΔF/F across cells (population variability)
        "sig_peak_rate",   # fraction of cells above 2σ threshold
        "sig_temporal_d",  # temporal derivative (mean change from prev window)
        "sig_sync",        # population synchrony (1 - CV)
        "sig_range",       # max - min ΔF/F (dynamic range)
    ]

    def __init__(self, learning_rate=0.02, frozen=False):
        """Initialize with default Hebbian weights.

        Args:
            learning_rate: η for Hebbian weight updates during calibration.
            frozen: if True, weights are not updated (inference mode).
        """
        self.lr = learning_rate
        self.frozen = frozen
        self._trained_windows = 0

        # W_signal: [6 signal features] → [7 z_t cost dimensions]
        # Initialized with biologically-motivated priors:
        #   sig_mean → potential_displacement (higher signal = more potential)
        #   sig_std → drift_cost (variability = drift in signal space)
        #   sig_peak_rate → transition_cost (bursts = state transitions)
        #   sig_temporal_d → gamma_desync (temporal change = desync)
        #   sig_sync → xin_residual (async = unresolved residual)
        #   sig_range → cross_slice_churn (wide range = churn)
        self.W = [
            # transition  drift   gamma   xin     potential  churn   magnitude
            [0.05,       0.10,   0.05,   0.05,   0.30,     0.05,   0.10],  # sig_mean
            [0.10,       0.30,   0.10,   0.10,   0.10,     0.10,   0.10],  # sig_std
            [0.30,       0.05,   0.10,   0.05,   0.10,     0.05,   0.20],  # sig_peak_rate
            [0.10,       0.10,   0.30,   0.10,   0.10,     0.10,   0.10],  # sig_temporal_d
            [0.05,       0.10,   0.10,   0.30,   0.05,     0.10,   0.05],  # sig_sync
            [0.10,       0.10,   0.05,   0.10,   0.05,     0.30,   0.15],  # sig_range
        ]

        # Running statistics for normalization
        self._sig_prev_mean = None
        self._measure_time = None

    def _ensure_measure_time(self):
        """Lazy import to avoid circular dependency."""
        if self._measure_time is None:
            try:
                from engines._common import InternalMeasureTime, MeasureCoordinate
                self._measure_time = InternalMeasureTime()
                self._MeasureCoordinate = MeasureCoordinate
            except ImportError:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent / "engines"))
                from _common import InternalMeasureTime, MeasureCoordinate
                self._measure_time = InternalMeasureTime()
                self._MeasureCoordinate = MeasureCoordinate

    def extract_signal_features(self, signal_values):
        """Compute 6 signal features from raw ΔF/F values.

        Returns:
            features: list of 6 floats
        """
        n = len(signal_values)
        if n == 0:
            return [0.0] * 6

        sig_mean = sum(signal_values) / n
        sig_var = sum((s - sig_mean) ** 2 for s in signal_values) / n
        sig_std = math.sqrt(sig_var)

        # Peak rate: fraction of cells above 2σ
        threshold = sig_mean + 2 * max(sig_std, 0.01)
        sig_peak_rate = sum(1 for s in signal_values if s > threshold) / n

        # Temporal derivative (requires previous mean)
        if self._sig_prev_mean is not None:
            sig_temporal_d = abs(sig_mean - self._sig_prev_mean)
        else:
            sig_temporal_d = 0.0
        self._sig_prev_mean = sig_mean

        # Synchrony: 1 - CV (coefficient of variation)
        cv = sig_std / max(abs(sig_mean), 0.01)
        sig_sync = max(0.0, 1.0 - min(1.0, cv))

        # Dynamic range
        sig_range = max(signal_values) - min(signal_values)

        return [sig_mean, sig_std, sig_peak_rate,
                sig_temporal_d, sig_sync, sig_range]

    def signal_to_z_t(self, signal_features):
        """Map signal features to MeasureCoordinate z_t via Hebbian weights.

        z_t[j] = Σ_i W[i][j] · signal_feature[i]

        Returns:
            MeasureCoordinate z_t
        """
        self._ensure_measure_time()
        costs = [0.0] * 7
        for i in range(min(len(signal_features), 6)):
            for j in range(7):
                costs[j] += self.W[i][j] * signal_features[i]

        return self._MeasureCoordinate(
            transition_cost=costs[0],
            drift_cost=costs[1],
            gamma_desync_cost=costs[2],
            xin_residual_cost=costs[3],
            potential_displacement_cost=costs[4],
            cross_slice_churn_cost=costs[5],
            magnitude_disturbance_cost=costs[6],
        )

    def transform(self, signal_values):
        """Full transform chain: signal → z_t → Φ → d_σ_t → (disp, spread).

        Returns:
            disp_proxy: d_σ_t-derived displacement (replaces raw sig_std * 2)
            spread_proxy: Φ-derived spread (replaces raw sig_var * 5)
            z_t: the MeasureCoordinate for audit/logging
        """
        self._ensure_measure_time()

        # Step 1: Raw signal → 6 features
        sig_features = self.extract_signal_features(signal_values)

        # Step 2: Signal features → z_t via Hebbian weights W
        z_t = self.signal_to_z_t(sig_features)

        # Step 3: z_t → Φ(t) (motion potential)
        phi = z_t.to_phi()

        # Step 4: z_t → d_σ_t (spacetime measure increment)
        d_sigma = self._measure_time.compute_from_z(z_t)

        # Step 5: Map to displacement-like quantities
        #   disp_proxy = d_σ_t (spacetime distance traversed)
        #   spread_proxy = Φ (motion potential = uncertainty spread)
        disp_proxy = max(0.001, d_sigma * 0.1)  # scale to displacement range
        spread_proxy = max(0.001, phi * 0.5)

        return disp_proxy, spread_proxy, z_t

    def hebbian_update(self, signal_features, z_t, reward_signal=1.0):
        """Oja-rule update for W_signal based on co-activation.

        Implements: ΔW[i][j] = η · sig_feature[i] · (z_t[j] - W[i][j] · sig_feature[i])

        This is the Hebbian learning that "trains and fixes" the transform.
        After calibration, call freeze() to lock the weights.

        Args:
            signal_features: the 6-dim signal input
            z_t: the resulting MeasureCoordinate
            reward_signal: modulation (1.0 = normal, <1 = weak, >1 = strong)
        """
        if self.frozen:
            return

        z_vals = list(z_t.as_tuple())
        for i in range(min(len(signal_features), 6)):
            for j in range(7):
                # Oja rule: self-normalizing
                delta = self.lr * reward_signal * signal_features[i] * (
                    z_vals[j] - self.W[i][j] * signal_features[i])
                self.W[i][j] = max(0.0, min(1.0, self.W[i][j] + delta))

        self._trained_windows += 1

    def freeze(self):
        """Freeze the Hebbian weights after calibration training."""
        self.frozen = True

    def get_weight_summary(self):
        """Return the current W matrix for audit."""
        return {
            "W": [[round(w, 6) for w in row] for row in self.W],
            "trained_windows": self._trained_windows,
            "frozen": self.frozen,
            "feature_names": self.SIGNAL_FEATURES,
            "cost_dims": ["transition", "drift", "gamma_desync",
                          "xin_residual", "potential_displacement",
                          "cross_slice_churn", "magnitude_disturbance"],
        }


class FeatureExtractor:
    """Extracts an 8-dimensional feature vector from cell motion data.

    Phase 3.1 upgrade: supports signal_values parameter for neural data.

    ARCHITECTURAL NOTE (2026.5.14 review):
      When spatial displacement ≈ 0 (e.g., calcium imaging), signal_values
      are NOT directly used as displacement. Instead, they pass through the
      HebbianSignalTransform which implements the canonical chain:

        ΔF/F → signal_features(6d) → z_t(7d) via W_signal → Φ(t) → d_σ_t → disp_proxy

      The W_signal weights are a Hebbian hypergraph mapping signal-space
      features to the 7-dimensional MeasureCoordinate cost space. These
      weights are trainable during calibration and frozen for inference,
      ensuring the proxy relationship is explicit, learned, and auditable.
    """

    def __init__(self):
        self.feature_history = []
        self.displacement_buffer = []
        self.signal_buffer = []
        # Phase 3.1: Hebbian-mediated signal transform
        self._signal_transform = HebbianSignalTransform()

    def extract(self, positions_prev, positions_curr, displacements,
                signal_values=None):
        """Extract features from motion and/or signal data.

        Args:
            positions_prev: {cell_id: (x, y)} at window k-1
            positions_curr: {cell_id: (x, y)} at window k
            displacements:  {cell_id: float} spatial displacements
            signal_values:  optional list of signal intensities (e.g., ΔF/F)
                           — when provided and spatial displacement is near zero,
                           these pass through HebbianSignalTransform to produce
                           d_σ_t-based displacement proxies (NOT raw variance).
        """
        n = len(displacements)
        disp_vals = list(displacements.values())
        disp_mean = sum(disp_vals) / max(n, 1)
        disp_std = math.sqrt(sum((d - disp_mean)**2 for d in disp_vals) / max(n, 1))

        # Phase 3.1: When spatial displacement ≈ 0 and we have signal data,
        # use HebbianSignalTransform to map signal → d_σ_t → displacement proxy.
        # This is NOT a naive variance substitution — it passes through the
        # Hebbian-calibrated z_t → Φ → d_σ_t chain.
        use_signal = (signal_values is not None and
                      len(signal_values) >= 2 and
                      disp_mean < 0.01)

        if use_signal:
            # Full Hebbian-mediated transform chain
            disp_proxy, spread_proxy, z_t = self._signal_transform.transform(
                signal_values)

            # Hebbian update during training (not frozen)
            sig_features = self._signal_transform.extract_signal_features(
                signal_values)
            self._signal_transform.hebbian_update(sig_features, z_t)

            disp_mean = disp_proxy
            disp_std = spread_proxy

            sig_mean = sum(signal_values) / len(signal_values)
            self.signal_buffer.append(sig_mean)
        else:
            self.signal_buffer.append(disp_mean)

        self.displacement_buffer.append(disp_mean)

        # Velocity coherence
        vecs = []
        for i in range(n):
            if i in positions_prev and i in positions_curr:
                dx = positions_curr[i][0] - positions_prev[i][0]
                dy = positions_curr[i][1] - positions_prev[i][1]
                vecs.append((dx, dy))

        if use_signal and signal_values:
            # For signal data: coherence = how synchronized the cells are
            # (low variance across cells = high coherence)
            _sig_mean = sum(signal_values) / len(signal_values)
            _sig_var = sum((s - _sig_mean) ** 2 for s in signal_values) / len(signal_values)
            _sig_std = math.sqrt(_sig_var)
            sig_cv = _sig_std / max(abs(_sig_mean), 0.01)
            coherence = max(0.0, 1.0 - min(1.0, sig_cv))
        elif len(vecs) >= 2:
            avg_vx = sum(v[0] for v in vecs) / len(vecs)
            avg_vy = sum(v[1] for v in vecs) / len(vecs)
            mag = math.sqrt(avg_vx**2 + avg_vy**2) + 1e-8
            coherence = sum(abs(v[0]*avg_vx + v[1]*avg_vy) /
                          (math.sqrt(v[0]**2+v[1]**2+1e-8) * mag)
                          for v in vecs) / len(vecs)
        else:
            coherence = 0.0

        # Periodicity
        periodicity = 0.0
        buf_for_period = self.signal_buffer if use_signal else [
            f[0] for f in self.feature_history] if self.feature_history else []

        if len(self.feature_history) >= 8:
            recent = [f[0] for f in self.feature_history[-8:]]
            mean_r = sum(recent) / len(recent)
            num = sum((recent[i]-mean_r)*(recent[i+4]-mean_r) for i in range(4))
            den = sum((r-mean_r)**2 for r in recent) + 1e-8
            periodicity = max(0, num / den)

        # Jump indicator
        jump_score = 0.0
        if len(self.feature_history) >= 1:
            prev_disp = self.feature_history[-1][0]
            if disp_mean > prev_disp * 3 + 0.1:
                jump_score = min(1.0, (disp_mean - prev_disp) / 2.0)

        # Frequency energy
        freq_energy = 0.0
        if len(self.displacement_buffer) >= 6:
            buf = self.displacement_buffer[-6:]
            bm = sum(buf) / len(buf)
            freq_energy = sum((b - bm)**2 for b in buf) / len(buf)

        # Acceleration
        accel = 0.0
        if len(self.displacement_buffer) >= 3:
            accel = abs(self.displacement_buffer[-1] - 2*self.displacement_buffer[-2]
                        + self.displacement_buffer[-3])

        # Velocity consistency
        vel_consistency = 0.0
        if use_signal and len(self.signal_buffer) >= 3:
            # For signal data: consistency = how stable the mean signal is
            recent_sigs = self.signal_buffer[-3:]
            rs_mean = sum(recent_sigs) / len(recent_sigs)
            rs_std = math.sqrt(sum((s - rs_mean) ** 2 for s in recent_sigs) / len(recent_sigs))
            vel_consistency = 1.0 - min(1.0, rs_std / max(abs(rs_mean), 0.01))
        elif len(vecs) >= 2:
            mags = [math.sqrt(v[0]**2 + v[1]**2) for v in vecs]
            mag_mean = sum(mags) / len(mags)
            mag_std = math.sqrt(sum((m - mag_mean)**2 for m in mags) / len(mags))
            vel_consistency = 1.0 - min(1.0, mag_std / max(mag_mean, 0.01))

        vec = (disp_mean, disp_std, coherence, periodicity,
               jump_score, freq_energy, accel, vel_consistency)
        self.feature_history.append(vec)
        return vec


# ═══════════════════════════════════════════════════════════════
# 3. Online Bayesian Recognizer (replaces lookup-table)
# ═══════════════════════════════════════════════════════════════

class BayesianMotionRecognizer:
    """Online Bayesian classifier for motion states.

    For each regime k, maintains:
      n_k:   count of observations
      mu_k:  running mean of feature vector (8-dim)
      var_k: running variance of each feature dimension

    Classification uses log-posterior:
      log p(k|x) = log pi_k + log N(x | mu_k, diag(var_k))
    """

    def __init__(self, prior_var=1.0):
        self.regimes = list(MOTION_REGIMES.keys())
        self.n_dim = len(FEATURE_NAMES)
        self.prior_var = prior_var
        # Per-regime sufficient statistics
        self.n_k = {r: 0 for r in self.regimes}
        self.mu_k = {r: [0.0] * self.n_dim for r in self.regimes}
        self.var_k = {r: [prior_var] * self.n_dim for r in self.regimes}
        self.recognition_delay = 3
        self.correct_history = []

    def classify(self, feature_vec):
        """Bayesian classification using Gaussian likelihood."""
        log_posteriors = {}
        total_obs = sum(self.n_k.values()) + len(self.regimes)  # +smoothing

        for r in self.regimes:
            # Log prior (proportional to observation count)
            log_prior = math.log((self.n_k[r] + 1) / total_obs)

            # Log likelihood: sum of log N(x_d | mu_d, var_d) per dimension
            log_lik = 0.0
            for d in range(self.n_dim):
                v = max(self.var_k[r][d], 1e-6)
                diff = feature_vec[d] - self.mu_k[r][d]
                log_lik += -0.5 * math.log(2 * math.pi * v) - 0.5 * diff**2 / v

            log_posteriors[r] = log_prior + log_lik

        # Normalize to get probabilities (log-sum-exp)
        max_lp = max(log_posteriors.values())
        exp_sum = sum(math.exp(lp - max_lp) for lp in log_posteriors.values())
        log_norm = max_lp + math.log(exp_sum)

        posteriors = {r: math.exp(lp - log_norm)
                      for r, lp in log_posteriors.items()}

        predicted = max(posteriors, key=posteriors.get)
        confidence = posteriors[predicted]
        return predicted, confidence, posteriors

    def learn(self, feature_vec, true_regime):
        """Online Bayesian update: Welford's algorithm for running mean/var."""
        r = true_regime
        self.n_k[r] += 1
        n = self.n_k[r]
        for d in range(self.n_dim):
            x = feature_vec[d]
            old_mu = self.mu_k[r][d]
            # Update mean
            new_mu = old_mu + (x - old_mu) / n
            self.mu_k[r][d] = new_mu
            # Update variance (Welford's online algorithm)
            if n >= 2:
                self.var_k[r][d] = (self.var_k[r][d] * (n - 2) / (n - 1)
                                    + (x - old_mu) * (x - new_mu) / (n - 1))
            # Floor variance to prevent collapse
            self.var_k[r][d] = max(self.var_k[r][d], 1e-4)

    def update_recognition_delay(self, k, correct):
        self.correct_history.append(correct)
        if len(self.correct_history) >= 5:
            recent_acc = sum(self.correct_history[-5:]) / 5
            if recent_acc >= 0.8 and self.recognition_delay > 1:
                self.recognition_delay = max(1, self.recognition_delay - 1)
            elif recent_acc < 0.4 and self.recognition_delay < 5:
                self.recognition_delay += 1

    def get_params_summary(self):
        """Return human-readable summary of learned distributions."""
        summary = {}
        for r in self.regimes:
            if self.n_k[r] > 0:
                summary[r] = {
                    "n": self.n_k[r],
                    "mu": [round(m, 4) for m in self.mu_k[r]],
                    "std": [round(math.sqrt(v), 4) for v in self.var_k[r]],
                }
        return summary


# ═══════════════════════════════════════════════════════════════
# 4. Legacy recognizer (kept for comparison, renamed)
# ═══════════════════════════════════════════════════════════════

class LegacyLookupRecognizer:
    """Original lookup-table recognizer. Kept for A/B comparison."""

    def __init__(self):
        self.feature_history = []
        self.hebbian_memory = {}
        self.recognition_delay = 3
        self.correct_history = []

    def classify(self, feature_vec):
        d, std, coh, per, jmp = feature_vec[0], feature_vec[1], feature_vec[2], feature_vec[3], feature_vec[4]
        scores = {}
        scores["stationary"]  = max(0, 1.0 - d * 10) * 1.2
        scores["slow_drift"]  = max(0, 1.0 - abs(d - 0.06) * 15) * coh * 2
        scores["fast_drift"]  = max(0, 1.0 - abs(d - 0.22) * 8) * coh * 2
        scores["oscillation"] = per * 3.0 + max(0, 1.0 - abs(d - 0.15) * 10) * 0.5
        scores["jump"]        = jmp * 5.0
        scores["diffusion"]   = max(0, 1.0 - abs(d - 0.15) * 10) * (1 - coh) * 2 * (1 - per)

        fkey = (round(d, 1), round(coh, 1), round(per, 1), round(jmp, 1))
        for regime in scores:
            mem_key = (regime, fkey)
            if mem_key in self.hebbian_memory:
                scores[regime] += self.hebbian_memory[mem_key] * 2.0

        predicted = max(scores, key=scores.get)
        confidence = scores[predicted] / (sum(scores.values()) + 1e-8)
        return predicted, confidence, scores

    def learn(self, feature_vec, true_regime):
        d, coh, per, jmp = feature_vec[0], feature_vec[2], feature_vec[3], feature_vec[4]
        fkey = (round(d, 1), round(coh, 1), round(per, 1), round(jmp, 1))
        mem_key = (true_regime, fkey)
        self.hebbian_memory[mem_key] = self.hebbian_memory.get(mem_key, 0) + 0.3

    def update_recognition_delay(self, k, correct):
        self.correct_history.append(correct)
        if len(self.correct_history) >= 5:
            recent_acc = sum(self.correct_history[-5:]) / 5
            if recent_acc >= 0.8 and self.recognition_delay > 1:
                self.recognition_delay = max(1, self.recognition_delay - 1)
            elif recent_acc < 0.4 and self.recognition_delay < 5:
                self.recognition_delay += 1


# Legacy alias for backward compatibility
MotionStateRecognizer = LegacyLookupRecognizer


# ═══════════════════════════════════════════════════════════════
# 3. Async→Sync Convergence Experiment
# ═══════════════════════════════════════════════════════════════

def run_motion_recognition_experiment(conn, run_id, total_windows=60, n_cells=40, seed=42):
    """Full experiment: generate motion, recognize, track async→sync."""

    gen = MotionProcessGenerator(total_windows=total_windows, n_cells=n_cells, seed=seed)
    rec = MotionStateRecognizer()
    prev_positions = None

    results = []
    phase_stats = {"async": [], "transition": [], "sync": []}

    for k in range(total_windows):
        state, positions, displacements = gen.step(k)
        true_regime = state.regime

        if prev_positions is not None:
            features = rec.extract_features(prev_positions, positions, displacements)
            predicted, confidence, scores = rec.classify(features)

            # Determine if recognition uses delay
            delay = rec.recognition_delay
            phase = "async" if delay >= 3 else ("transition" if delay == 2 else "sync")
            correct = (predicted == true_regime)

            rec.learn(features, true_regime, predicted)
            rec.update_recognition_delay(k, correct)

            result = {
                "window": k, "true_regime": true_regime,
                "predicted": predicted, "correct": correct,
                "confidence": round(confidence, 3),
                "delay": delay, "phase": phase,
                "displacement": round(state.displacement, 4),
                "scores": {r: round(s, 3) for r, s in scores.items()},
                "memory_size": len(rec.hebbian_memory),
            }
            results.append(result)
            phase_stats[phase].append(correct)

            # Write to DB
            conn.execute(
                "INSERT INTO v37417_motion_recognition_log "
                "(record_id,run_id,window_k,true_regime,predicted_regime,"
                "correct,confidence,delay,phase,displacement,"
                "scores_json,memory_size,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (_jid("mr"), run_id, k, true_regime, predicted,
                 1 if correct else 0, confidence, delay, phase,
                 state.displacement, json.dumps(result["scores"]),
                 len(rec.hebbian_memory), _now()))

        prev_positions = dict(positions)

    # Compute phase accuracies
    acc = {}
    for phase_name, corrects in phase_stats.items():
        if corrects:
            acc[phase_name] = round(sum(corrects) / len(corrects), 3)
        else:
            acc[phase_name] = 0

    # Regime-level accuracy
    regime_acc = {}
    for r in MOTION_REGIMES:
        matches = [x for x in results if x["true_regime"] == r]
        if matches:
            regime_acc[r] = round(sum(1 for m in matches if m["correct"]) / len(matches), 3)

    # Convergence analysis: sliding window accuracy
    window_size = 5
    sliding_acc = []
    for i in range(len(results) - window_size + 1):
        chunk = results[i:i+window_size]
        sliding_acc.append(round(sum(1 for c in chunk if c["correct"]) / window_size, 2))

    # Write summary
    summary = {
        "total_windows": total_windows,
        "overall_accuracy": round(sum(1 for r in results if r["correct"]) / max(len(results),1), 3),
        "phase_accuracy": acc,
        "regime_accuracy": regime_acc,
        "final_delay": rec.recognition_delay,
        "memory_entries": len(rec.hebbian_memory),
        "sliding_accuracy": sliding_acc,
        "delay_evolution": [r["delay"] for r in results],
        "phase_evolution": [r["phase"] for r in results],
    }

    conn.execute(
        "INSERT INTO v37417_motion_experiment_summary "
        "(summary_id,run_id,total_windows,overall_accuracy,"
        "async_accuracy,transition_accuracy,sync_accuracy,"
        "final_delay,memory_entries,regime_accuracy_json,"
        "sliding_accuracy_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (_jid("mes"), run_id, total_windows,
         summary["overall_accuracy"],
         acc.get("async", 0), acc.get("transition", 0), acc.get("sync", 0),
         rec.recognition_delay, len(rec.hebbian_memory),
         json.dumps(regime_acc), json.dumps(sliding_acc), _now()))

    return summary, results
