#!/usr/bin/env python3
"""Motion Recognition Diagnostic & Recursive Improvement Experiment.

1. Confusion matrix analysis — which regimes are confused and why
2. Feature overlap analysis — root cause of weak discrimination
3. Multi-pass recursive testing — does accuracy improve with repetition?
4. Enhanced features — frequency domain + higher-order stats
"""
from __future__ import annotations
import sqlite3, sys, json, time, math, random, uuid, copy
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
REPORT_DIR = ROOT / "v37417_motion_diagnostic_reports"
REPORT_DIR.mkdir(exist_ok=True)

from motion_recognition_engine import (
    MotionProcessGenerator, MotionStateRecognizer, MOTION_REGIMES,
    run_motion_recognition_experiment)

def now(): return datetime.now(timezone.utc).isoformat()

# ═══════════════════════════════════════════════════════════════
# Phase 1: Confusion Matrix & Error Analysis
# ═══════════════════════════════════════════════════════════════
def analyze_confusion(results):
    """Build confusion matrix and identify error patterns."""
    matrix = defaultdict(lambda: defaultdict(int))
    errors = []
    for r in results:
        matrix[r["true_regime"]][r["predicted"]] += 1
        if not r["correct"]:
            errors.append(r)
    return dict(matrix), errors

def analyze_feature_overlap(results, gen):
    """Analyze which features overlap between confused regimes."""
    regime_features = defaultdict(list)
    for r in results:
        regime_features[r["true_regime"]].append(r.get("displacement", 0))

    # Compute feature distributions per regime
    distributions = {}
    for regime, disps in regime_features.items():
        if disps:
            mean = sum(disps) / len(disps)
            std = math.sqrt(sum((d - mean)**2 for d in disps) / max(len(disps), 1))
            distributions[regime] = {"mean": round(mean, 4), "std": round(std, 4),
                                     "min": round(min(disps), 4), "max": round(max(disps), 4)}
    # Pairwise overlap
    overlaps = {}
    regimes = list(distributions.keys())
    for i, r1 in enumerate(regimes):
        for r2 in regimes[i+1:]:
            d1, d2 = distributions[r1], distributions[r2]
            # Simple overlap: do ranges intersect?
            lo = max(d1["mean"] - d1["std"], d2["mean"] - d2["std"])
            hi = min(d1["mean"] + d1["std"], d2["mean"] + d2["std"])
            overlap = max(0, hi - lo)
            span = max(d1["mean"] + d1["std"], d2["mean"] + d2["std"]) - min(d1["mean"] - d1["std"], d2["mean"] - d2["std"])
            overlap_pct = overlap / max(span, 0.001)
            overlaps[f"{r1}_vs_{r2}"] = round(overlap_pct, 3)
    return distributions, overlaps


# ═══════════════════════════════════════════════════════════════
# Phase 2: Enhanced Recognizer with Frequency & Higher-Order
# ═══════════════════════════════════════════════════════════════
class EnhancedMotionRecognizer(MotionStateRecognizer):
    """Adds frequency-domain and higher-order statistical features."""

    def __init__(self):
        super().__init__()
        self.displacement_buffer = []  # rolling buffer for FFT proxy
        self.velocity_buffer = []

    def extract_features(self, positions_prev, positions_curr, displacements):
        """Extract enhanced features including frequency and kurtosis."""
        base = super().extract_features(positions_prev, positions_curr, displacements)

        disp_vals = list(displacements.values())
        self.displacement_buffer.append(sum(disp_vals) / max(len(disp_vals), 1))
        n = len(disp_vals)

        # Higher-order statistics
        mean = base["disp_mean"]
        if n > 2:
            var = sum((d - mean)**2 for d in disp_vals) / n
            std = math.sqrt(var) + 1e-8
            skewness = sum(((d - mean) / std)**3 for d in disp_vals) / n
            kurtosis = sum(((d - mean) / std)**4 for d in disp_vals) / n - 3
        else:
            skewness = 0; kurtosis = 0

        # Frequency proxy: variance of recent displacements (high = oscillation)
        freq_energy = 0.0
        if len(self.displacement_buffer) >= 6:
            recent = self.displacement_buffer[-6:]
            rmean = sum(recent) / len(recent)
            freq_energy = sum((r - rmean)**2 for r in recent) / len(recent)

        # Acceleration: change in displacement
        accel = 0.0
        if len(self.displacement_buffer) >= 3:
            accel = self.displacement_buffer[-1] - 2*self.displacement_buffer[-2] + self.displacement_buffer[-3]

        # Velocity consistency across cells (distinguish diffusion from drift)
        vecs = []
        for i in range(min(n, len(positions_prev), len(positions_curr))):
            if i in positions_prev and i in positions_curr:
                dx = positions_curr[i][0] - positions_prev[i][0]
                dy = positions_curr[i][1] - positions_prev[i][1]
                vecs.append((dx, dy))
        vel_consistency = 0.0
        if len(vecs) >= 2:
            mags = [math.sqrt(v[0]**2 + v[1]**2) for v in vecs]
            mag_mean = sum(mags) / len(mags)
            mag_std = math.sqrt(sum((m - mag_mean)**2 for m in mags) / len(mags))
            vel_consistency = 1.0 - min(1.0, mag_std / max(mag_mean, 0.01))

        base["skewness"] = skewness
        base["kurtosis"] = kurtosis
        base["freq_energy"] = freq_energy
        base["accel"] = abs(accel)
        base["vel_consistency"] = vel_consistency
        return base

    def classify(self, features):
        """Enhanced classification using all features."""
        d = features["disp_mean"]
        std = features["disp_std"]
        coh = features["coherence"]
        per = features["periodicity"]
        jmp = features["jump_score"]
        freq = features.get("freq_energy", 0)
        kurt = features.get("kurtosis", 0)
        accel = features.get("accel", 0)
        vc = features.get("vel_consistency", 0)

        scores = {}
        scores["stationary"]  = max(0, 1.0 - d * 10) * 1.5
        scores["slow_drift"]  = max(0, 1.0 - abs(d - 0.06) * 12) * coh * 2 * vc
        scores["fast_drift"]  = max(0, 1.0 - abs(d - 0.22) * 6) * coh * 2 * vc
        scores["oscillation"] = (per * 3.0 + freq * 8.0 +
                                 max(0, accel) * 2.0 +
                                 max(0, 1.0 - abs(d - 0.15) * 8) * 0.3)
        scores["jump"]        = (jmp * 5.0 +
                                 max(0, kurt - 1) * 1.5 +
                                 max(0, features["disp_std"] - 0.3) * 3.0)
        scores["diffusion"]   = (max(0, 1.0 - abs(d - 0.12) * 8) * (1 - coh) * 2 * (1 - per) *
                                 (1 - vc + 0.3) +
                                 max(0, std - 0.05) * 2.0 * (1 - coh))

        # Memory augmentation
        fkey = self._feature_key(features)
        for regime in scores:
            mem_key = (regime, fkey)
            if mem_key in self.hebbian_memory:
                scores[regime] += self.hebbian_memory[mem_key] * 2.0

        predicted = max(scores, key=scores.get)
        total = sum(scores.values()) + 1e-8
        confidence = scores[predicted] / total
        return predicted, confidence, scores

    def _feature_key(self, f):
        """Enhanced discretization including new features."""
        return (round(f["disp_mean"], 1), round(f["coherence"], 1),
                round(f["periodicity"], 1), round(f["jump_score"], 1),
                round(f.get("freq_energy", 0), 1),
                round(f.get("vel_consistency", 0), 1))


# ═══════════════════════════════════════════════════════════════
# Phase 3: Multi-Pass Recursive Experiment
# ═══════════════════════════════════════════════════════════════
def run_single_pass(gen_seed, recognizer_class, pass_number, prev_memory=None):
    """Run one pass of 60-window recognition."""
    gen = MotionProcessGenerator(total_windows=60, n_cells=40, seed=gen_seed)
    rec = recognizer_class()
    if prev_memory:
        rec.hebbian_memory = copy.deepcopy(prev_memory)

    prev_pos = None
    results = []
    for k in range(60):
        state, positions, displacements = gen.step(k)
        if prev_pos is not None:
            features = rec.extract_features(prev_pos, positions, displacements)
            predicted, confidence, scores = rec.classify(features)
            correct = (predicted == state.regime)
            rec.learn(features, state.regime, predicted)
            rec.update_recognition_delay(k, correct)
            results.append({
                "window": k, "true_regime": state.regime,
                "predicted": predicted, "correct": correct,
                "confidence": round(confidence, 3),
                "delay": rec.recognition_delay,
            })
        prev_pos = dict(positions)

    total = len(results)
    acc = sum(1 for r in results if r["correct"]) / max(total, 1)
    regime_acc = {}
    for regime in MOTION_REGIMES:
        matches = [r for r in results if r["true_regime"] == regime]
        if matches:
            regime_acc[regime] = round(sum(1 for m in matches if m["correct"]) / len(matches), 3)

    return {
        "pass": pass_number,
        "accuracy": round(acc, 3),
        "regime_accuracy": regime_acc,
        "memory_size": len(rec.hebbian_memory),
        "final_delay": rec.recognition_delay,
        "results": results,
    }, rec.hebbian_memory


def main():
    t0 = time.time()
    print("=" * 80)
    print("MOTION RECOGNITION DIAGNOSTIC & RECURSIVE IMPROVEMENT")
    print("=" * 80)

    # === Phase 1: Baseline + Confusion Analysis ===
    print("\n--- Phase 1: Baseline Error Analysis ---")
    gen = MotionProcessGenerator(total_windows=60, n_cells=40, seed=42)
    rec = MotionStateRecognizer()
    prev_pos = None; results = []
    for k in range(60):
        state, positions, displacements = gen.step(k)
        if prev_pos is not None:
            features = rec.extract_features(prev_pos, positions, displacements)
            predicted, confidence, scores = rec.classify(features)
            correct = (predicted == state.regime)
            rec.learn(features, state.regime, predicted)
            rec.update_recognition_delay(k, correct)
            results.append({"window": k, "true_regime": state.regime,
                           "predicted": predicted, "correct": correct,
                           "confidence": round(confidence, 3),
                           "displacement": round(state.displacement, 4),
                           "scores": {r: round(s, 3) for r, s in scores.items()}})
        prev_pos = dict(positions)

    matrix, errors = analyze_confusion(results)
    distributions, overlaps = analyze_feature_overlap(results, gen)

    print(f"\n  Confusion Matrix:")
    regimes = sorted(MOTION_REGIMES.keys())
    true_pred_label = "True \\ Pred"
    header = f"  {true_pred_label:>15s}" + "".join(f" {r[:8]:>8s}" for r in regimes)
    print(header)
    for true_r in regimes:
        row = f"  {true_r:>15s}"
        for pred_r in regimes:
            cnt = matrix.get(true_r, {}).get(pred_r, 0)
            mark = f" {cnt:>8d}" if cnt > 0 else "        ."
            row += mark
        print(row)

    print(f"\n  Feature Distributions (displacement):")
    for regime, dist in sorted(distributions.items()):
        print(f"    {regime:15s}: mean={dist['mean']:.4f} std={dist['std']:.4f} [{dist['min']:.4f}, {dist['max']:.4f}]")

    print(f"\n  Feature Overlap (displacement 1-sigma):")
    for pair, olap in sorted(overlaps.items(), key=lambda x: -x[1]):
        flag = " ** HIGH **" if olap > 0.3 else ""
        print(f"    {pair:35s}: {olap*100:5.1f}%{flag}")

    # Error detail
    print(f"\n  Error Analysis ({len(errors)} errors):")
    error_patterns = defaultdict(int)
    for e in errors:
        error_patterns[f"{e['true_regime']} -> {e['predicted']}"] += 1
    for pattern, count in sorted(error_patterns.items(), key=lambda x: -x[1]):
        true_r, pred_r = pattern.split(" -> ")
        # Root cause
        if true_r == "oscillation" and pred_r == "fast_drift":
            cause = "displacement similar + coherence high before periodicity detected"
        elif true_r == "oscillation" and pred_r == "diffusion":
            cause = "low coherence in oscillation overlaps with diffusion signature"
        elif true_r == "jump" and "stationary" in pred_r:
            cause = "non-jump windows look stationary (jump_prob=0.3)"
        elif true_r == "diffusion":
            cause = "displacement + low coherence overlaps oscillation/slow_drift"
        else:
            cause = "feature space overlap"
        print(f"    {pattern:30s}: {count:2d} errors  cause: {cause}")

    # === Phase 2: Recursive multi-pass test ===
    print(f"\n{'='*80}")
    print("Phase 2: RECURSIVE MULTI-PASS TEST")
    print(f"{'='*80}")
    print("  Testing: does accuracy improve with repeated exposure?\n")

    NUM_PASSES = 6
    seeds = [42, 137, 256, 42, 137, 42]  # repeat seeds to test memory transfer

    # Baseline (no memory)
    print("  [Baseline Recognizer]")
    baseline_memory = None
    baseline_results = []
    for p in range(NUM_PASSES):
        res, baseline_memory = run_single_pass(seeds[p], MotionStateRecognizer, p+1, baseline_memory)
        baseline_results.append(res)
        ra = res["regime_accuracy"]
        weak = [r for r, a in ra.items() if a < 0.5]
        print(f"    Pass {p+1}: acc={res['accuracy']*100:5.1f}%  mem={res['memory_size']:3d}  "
              f"delay={res['final_delay']}  weak={weak}")

    # Enhanced (with frequency + kurtosis)
    print("\n  [Enhanced Recognizer (+ frequency + kurtosis + velocity consistency)]")
    enhanced_memory = None
    enhanced_results = []
    for p in range(NUM_PASSES):
        res, enhanced_memory = run_single_pass(seeds[p], EnhancedMotionRecognizer, p+1, enhanced_memory)
        enhanced_results.append(res)
        ra = res["regime_accuracy"]
        weak = [r for r, a in ra.items() if a < 0.5]
        print(f"    Pass {p+1}: acc={res['accuracy']*100:5.1f}%  mem={res['memory_size']:3d}  "
              f"delay={res['final_delay']}  weak={weak}")

    # === Phase 3: Comparative Analysis ===
    print(f"\n{'='*80}")
    print("Phase 3: COMPARATIVE ANALYSIS")
    print(f"{'='*80}")

    print(f"\n  Accuracy Trajectory:")
    print(f"  {'Pass':>6s} {'Baseline':>10s} {'Enhanced':>10s} {'Delta':>8s}")
    for p in range(NUM_PASSES):
        b = baseline_results[p]["accuracy"]
        e = enhanced_results[p]["accuracy"]
        print(f"  {p+1:6d} {b*100:9.1f}% {e*100:9.1f}% {(e-b)*100:+7.1f}%")

    print(f"\n  Per-Regime Improvement (Pass 1 -> Pass {NUM_PASSES}):")
    print(f"  {'Regime':>15s} {'Base P1':>8s} {'Base P{0}':>8s} {'Enh P1':>8s} {'Enh P{0}':>8s} {'Verdict':>10s}".format(NUM_PASSES, NUM_PASSES))
    for regime in sorted(MOTION_REGIMES.keys()):
        b1 = baseline_results[0]["regime_accuracy"].get(regime, 0)
        bn = baseline_results[-1]["regime_accuracy"].get(regime, 0)
        e1 = enhanced_results[0]["regime_accuracy"].get(regime, 0)
        en = enhanced_results[-1]["regime_accuracy"].get(regime, 0)
        if en >= 0.8: verdict = "SOLVED"
        elif en > b1: verdict = "IMPROVED"
        elif en == b1: verdict = "NO CHANGE"
        else: verdict = "DEGRADED"
        print(f"  {regime:>15s} {b1*100:7.0f}% {bn*100:7.0f}% {e1*100:7.0f}% {en*100:7.0f}% {verdict:>10s}")

    # Memory growth
    print(f"\n  Memory Growth:")
    print(f"  {'Pass':>6s} {'Base mem':>10s} {'Enh mem':>10s}")
    for p in range(NUM_PASSES):
        print(f"  {p+1:6d} {baseline_results[p]['memory_size']:10d} {enhanced_results[p]['memory_size']:10d}")

    # Verdict
    b_final = baseline_results[-1]["accuracy"]
    e_final = enhanced_results[-1]["accuracy"]
    b_first = baseline_results[0]["accuracy"]
    e_first = enhanced_results[0]["accuracy"]
    b_improve = b_final - b_first
    e_improve = e_final - e_first

    print(f"\n{'='*80}")
    print("CONCLUSIONS")
    print(f"{'='*80}")
    print(f"  Baseline: {b_first*100:.1f}% -> {b_final*100:.1f}% ({b_improve*100:+.1f}% over {NUM_PASSES} passes)")
    print(f"  Enhanced: {e_first*100:.1f}% -> {e_final*100:.1f}% ({e_improve*100:+.1f}% over {NUM_PASSES} passes)")
    print(f"  Enhancement gain: {(e_final-b_final)*100:+.1f}% final accuracy")
    print(f"  Recursive gain:   {max(b_improve, e_improve)*100:+.1f}% best improvement")
    if e_improve > 0.05:
        print(f"  VERDICT: YES, recursive testing DOES improve accuracy")
    elif e_improve > 0:
        print(f"  VERDICT: MARGINAL improvement through recursive testing")
    else:
        print(f"  VERDICT: Recursive testing alone is INSUFFICIENT; feature enhancement needed")

    elapsed = time.time() - t0
    report = {
        "confusion_matrix": {k: dict(v) for k, v in matrix.items()},
        "feature_distributions": distributions,
        "feature_overlaps": overlaps,
        "error_patterns": dict(error_patterns),
        "baseline_trajectory": [r["accuracy"] for r in baseline_results],
        "enhanced_trajectory": [r["accuracy"] for r in enhanced_results],
        "baseline_regime_first": baseline_results[0]["regime_accuracy"],
        "baseline_regime_last": baseline_results[-1]["regime_accuracy"],
        "enhanced_regime_first": enhanced_results[0]["regime_accuracy"],
        "enhanced_regime_last": enhanced_results[-1]["regime_accuracy"],
        "verdict": {
            "recursive_helps": e_improve > 0,
            "enhancement_helps": e_final > b_final,
            "best_accuracy": max(e_final, b_final),
        },
        "elapsed_s": round(elapsed, 2),
    }
    with open(REPORT_DIR / "diagnostic_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Report: {REPORT_DIR}")
    print(f"  Elapsed: {elapsed:.1f}s")

if __name__ == "__main__":
    main()
