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
# 2. Motion State Recognizer (Upper Layer)
# ═══════════════════════════════════════════════════════════════

class MotionStateRecognizer:
    """Recognize motion states using FHPMS memory features.

    Features extracted per window:
    - displacement_mean, displacement_std
    - velocity_coherence (how aligned velocities are)
    - periodicity_score (autocorrelation proxy)
    - jump_indicator (sudden large displacement)
    """

    def __init__(self):
        self.feature_history = []
        self.hebbian_memory = {}  # (regime_label, feature_hash) -> strength
        self.prediction_buffer = []  # recent predictions
        self.recognition_delay = 3  # starts at 3 windows delay
        self.correct_history = []

    def extract_features(self, positions_prev, positions_curr, displacements):
        """Extract motion features from one window transition."""
        n = len(displacements)
        disp_vals = list(displacements.values())
        disp_mean = sum(disp_vals) / max(n, 1)
        disp_std = math.sqrt(sum((d - disp_mean)**2 for d in disp_vals) / max(n, 1))

        # Velocity coherence: cosine similarity of velocity vectors
        vecs = []
        for i in range(n):
            if i in positions_prev and i in positions_curr:
                dx = positions_curr[i][0] - positions_prev[i][0]
                dy = positions_curr[i][1] - positions_prev[i][1]
                vecs.append((dx, dy))
        if len(vecs) >= 2:
            avg_vx = sum(v[0] for v in vecs) / len(vecs)
            avg_vy = sum(v[1] for v in vecs) / len(vecs)
            mag = math.sqrt(avg_vx**2 + avg_vy**2) + 1e-8
            coherence = sum(abs(v[0]*avg_vx + v[1]*avg_vy) /
                          (math.sqrt(v[0]**2+v[1]**2+1e-8) * mag)
                          for v in vecs) / len(vecs)
        else:
            coherence = 0.0

        # Periodicity: check if displacement pattern repeats
        periodicity = 0.0
        if len(self.feature_history) >= 8:
            recent = [f["disp_mean"] for f in self.feature_history[-8:]]
            # Simple autocorrelation at lag 4
            mean_r = sum(recent) / len(recent)
            num = sum((recent[i]-mean_r)*(recent[i+4]-mean_r) for i in range(4))
            den = sum((r-mean_r)**2 for r in recent) + 1e-8
            periodicity = max(0, num / den)

        # Jump indicator
        jump_score = 0.0
        if len(self.feature_history) >= 1:
            prev_disp = self.feature_history[-1]["disp_mean"]
            if disp_mean > prev_disp * 3 + 0.1:
                jump_score = min(1.0, (disp_mean - prev_disp) / 2.0)

        features = {
            "disp_mean": disp_mean,
            "disp_std": disp_std,
            "coherence": coherence,
            "periodicity": periodicity,
            "jump_score": jump_score,
        }
        self.feature_history.append(features)
        return features

    def classify(self, features):
        """Rule-based + memory-augmented classification."""
        d = features["disp_mean"]
        std = features["disp_std"]
        coh = features["coherence"]
        per = features["periodicity"]
        jmp = features["jump_score"]

        # Score each regime
        scores = {}
        scores["stationary"]  = max(0, 1.0 - d * 10) * 1.2
        scores["slow_drift"]  = max(0, 1.0 - abs(d - 0.06) * 15) * coh * 2
        scores["fast_drift"]  = max(0, 1.0 - abs(d - 0.22) * 8) * coh * 2
        scores["oscillation"] = per * 3.0 + max(0, 1.0 - abs(d - 0.15) * 10) * 0.5
        scores["jump"]        = jmp * 5.0
        scores["diffusion"]   = max(0, 1.0 - abs(d - 0.15) * 10) * (1 - coh) * 2 * (1 - per)

        # Memory augmentation: boost scores of previously-seen patterns
        fkey = self._feature_key(features)
        for regime in scores:
            mem_key = (regime, fkey)
            if mem_key in self.hebbian_memory:
                scores[regime] += self.hebbian_memory[mem_key] * 2.0

        predicted = max(scores, key=scores.get)
        confidence = scores[predicted] / (sum(scores.values()) + 1e-8)
        return predicted, confidence, scores

    def _feature_key(self, f):
        """Discretize features into a hashable key for Hebbian lookup."""
        return (round(f["disp_mean"], 1), round(f["coherence"], 1),
                round(f["periodicity"], 1), round(f["jump_score"], 1))

    def learn(self, features, true_regime, predicted_regime):
        """Hebbian learning: strengthen correct associations."""
        fkey = self._feature_key(features)
        mem_key = (true_regime, fkey)
        self.hebbian_memory[mem_key] = self.hebbian_memory.get(mem_key, 0) + 0.3

        # Weaken incorrect
        if predicted_regime != true_regime:
            wrong_key = (predicted_regime, fkey)
            self.hebbian_memory[wrong_key] = max(0, self.hebbian_memory.get(wrong_key, 0) - 0.1)

    def update_recognition_delay(self, k, correct):
        """Adaptively reduce recognition delay as accuracy improves."""
        self.correct_history.append(correct)
        if len(self.correct_history) >= 5:
            recent_acc = sum(self.correct_history[-5:]) / 5
            if recent_acc >= 0.8 and self.recognition_delay > 1:
                self.recognition_delay = max(1, self.recognition_delay - 1)
            elif recent_acc < 0.4 and self.recognition_delay < 5:
                self.recognition_delay += 1


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
