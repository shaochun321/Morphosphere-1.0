#!/usr/bin/env python3
"""v38 Honest Baseline — Train/Test split evaluation with statistical rigor.

Phase 1.1 of the v38 improvement plan.

This runner provides an HONEST evaluation of the motion recognition system
by strictly separating training and testing data:

  Training seeds:  [42, 100, 200]  — learn Bayesian parameters here
  Testing seeds:   [500, 600, 700] — evaluate here, NO learning allowed

Reports:
  - Per-seed and aggregate accuracy ± std
  - Confusion matrix
  - 95% confidence interval
  - Per-regime precision/recall/F1
  - Comparison: Bayesian recognizer vs Legacy lookup vs Random baseline
"""
import os, sys, math, json, time
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE))

from motion_recognition_engine import (
    MotionProcessGenerator, FeatureExtractor,
    BayesianMotionRecognizer, LegacyLookupRecognizer,
    MOTION_REGIMES,
)

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

TRAIN_SEEDS = [42, 100, 200]
TEST_SEEDS = [500, 600, 700]
TOTAL_WINDOWS = 60
N_CELLS = 40


def run_single_seed(gen, recognizer, extractor, learn=True):
    """Run one full sequence, optionally learning. Returns list of results."""
    prev_positions = None
    results = []

    for k in range(gen.total_windows):
        state, positions, displacements = gen.step(k)
        true_regime = state.regime

        if prev_positions is not None:
            features = extractor.extract(prev_positions, positions, displacements)
            predicted, confidence, posteriors = recognizer.classify(features)
            correct = (predicted == true_regime)

            if learn:
                recognizer.learn(features, true_regime)
                recognizer.update_recognition_delay(k, correct)

            results.append({
                "window": k,
                "true": true_regime,
                "predicted": predicted,
                "correct": correct,
                "confidence": round(confidence, 4),
            })

        prev_positions = dict(positions)

    return results


def compute_confusion_matrix(results, regimes):
    """Build confusion matrix from results."""
    matrix = {true_r: {pred_r: 0 for pred_r in regimes} for true_r in regimes}
    for r in results:
        if r["true"] in matrix and r["predicted"] in matrix[r["true"]]:
            matrix[r["true"]][r["predicted"]] += 1
    return matrix


def compute_per_regime_metrics(confusion, regimes):
    """Compute precision, recall, F1 per regime from confusion matrix."""
    metrics = {}
    for regime in regimes:
        tp = confusion[regime][regime]
        fp = sum(confusion[other][regime] for other in regimes if other != regime)
        fn = sum(confusion[regime][other] for other in regimes if other != regime)

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)

        metrics[regime] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": tp + fn,
        }
    return metrics


def confidence_interval_95(accuracies):
    """Compute 95% CI from a list of accuracy values."""
    n = len(accuracies)
    if n < 2:
        return 0.0, 0.0
    mean = sum(accuracies) / n
    var = sum((a - mean) ** 2 for a in accuracies) / (n - 1)
    std = math.sqrt(var)
    # t-value for 95% CI with n-1 degrees of freedom (approx for small n)
    t_values = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571}
    t = t_values.get(n - 1, 1.96)
    margin = t * std / math.sqrt(n)
    return mean, margin


def main():
    print("=" * 72)
    print("Morphosphere v38 — HONEST BASELINE EVALUATION")
    print("Phase 1.1: Independent Train/Test Split")
    print("=" * 72)
    regimes = sorted(MOTION_REGIMES.keys())

    # ═══════════════════════════════════════════════════════════
    # Evaluator A: BayesianMotionRecognizer (the real test)
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 72)
    print("  EVALUATOR A: BayesianMotionRecognizer")
    print("─" * 72)

    bayesian_rec = BayesianMotionRecognizer(prior_var=1.0)

    # Phase 1: TRAIN on training seeds
    print(f"\n  Training on seeds: {TRAIN_SEEDS}")
    train_total = 0
    train_correct = 0
    for seed in TRAIN_SEEDS:
        gen = MotionProcessGenerator(
            total_windows=TOTAL_WINDOWS, n_cells=N_CELLS, seed=seed)
        extractor = FeatureExtractor()
        results = run_single_seed(gen, bayesian_rec, extractor, learn=True)
        acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
        train_total += len(results)
        train_correct += sum(1 for r in results if r["correct"])
        print(f"    seed={seed}: {len(results)} windows, "
              f"acc={acc:.3f}, "
              f"n_k={dict(bayesian_rec.n_k)}")

    train_acc = train_correct / max(train_total, 1)
    print(f"\n  Training accuracy (biased): {train_acc:.3f} "
          f"({train_correct}/{train_total})")
    print(f"  Learned distributions:")
    for regime in regimes:
        if bayesian_rec.n_k[regime] > 0:
            mu = [round(m, 3) for m in bayesian_rec.mu_k[regime][:4]]
            print(f"    {regime:12s}: n={bayesian_rec.n_k[regime]:3d}, "
                  f"mu[:4]={mu}")

    # Phase 2: TEST on test seeds (NO LEARNING!)
    print(f"\n  Testing on seeds: {TEST_SEEDS}  (NO LEARNING)")
    test_accuracies = []
    all_test_results = []

    for seed in TEST_SEEDS:
        gen = MotionProcessGenerator(
            total_windows=TOTAL_WINDOWS, n_cells=N_CELLS, seed=seed)
        extractor = FeatureExtractor()
        results = run_single_seed(gen, bayesian_rec, extractor, learn=False)
        acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
        test_accuracies.append(acc)
        all_test_results.extend(results)
        print(f"    seed={seed}: acc={acc:.3f} ({len(results)} windows)")

    mean_acc, margin = confidence_interval_95(test_accuracies)
    print(f"\n  ╔══════════════════════════════════════════════════════")
    print(f"  ║ TEST ACCURACY (Bayesian): {mean_acc:.3f} ± {margin:.3f}")
    print(f"  ║ 95% CI: [{mean_acc - margin:.3f}, {mean_acc + margin:.3f}]")
    print(f"  ║ Train/Test gap: {abs(train_acc - mean_acc):.3f}")
    print(f"  ╚══════════════════════════════════════════════════════")

    # Confusion matrix
    confusion = compute_confusion_matrix(all_test_results, regimes)
    print(f"\n  Confusion Matrix (rows=true, cols=predicted):")
    header = "          " + "".join(f"{r[:6]:>7s}" for r in regimes)
    print(f"  {header}")
    for true_r in regimes:
        row = f"  {true_r[:8]:>8s}"
        for pred_r in regimes:
            val = confusion[true_r][pred_r]
            row += f"{val:7d}"
        print(row)

    # Per-regime metrics
    regime_metrics = compute_per_regime_metrics(confusion, regimes)
    print(f"\n  Per-Regime Metrics:")
    print(f"  {'Regime':>12s} {'Prec':>6s} {'Recall':>7s} {'F1':>6s} {'Support':>8s}")
    for regime in regimes:
        m = regime_metrics[regime]
        print(f"  {regime:>12s} {m['precision']:6.3f} {m['recall']:7.3f} "
              f"{m['f1']:6.3f} {m['support']:8d}")

    # ═══════════════════════════════════════════════════════════
    # Evaluator B: LegacyLookupRecognizer (for comparison)
    # ═══════════════════════════════════════════════════════════
    print("\n" + "─" * 72)
    print("  EVALUATOR B: LegacyLookupRecognizer (baseline comparison)")
    print("─" * 72)

    legacy_rec = LegacyLookupRecognizer()

    # Train
    for seed in TRAIN_SEEDS:
        gen = MotionProcessGenerator(
            total_windows=TOTAL_WINDOWS, n_cells=N_CELLS, seed=seed)
        extractor = FeatureExtractor()
        results = run_single_seed(gen, legacy_rec, extractor, learn=True)

    # Test (no learning)
    legacy_test_accs = []
    for seed in TEST_SEEDS:
        gen = MotionProcessGenerator(
            total_windows=TOTAL_WINDOWS, n_cells=N_CELLS, seed=seed)
        extractor = FeatureExtractor()
        results = run_single_seed(gen, legacy_rec, extractor, learn=False)
        acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
        legacy_test_accs.append(acc)

    legacy_mean, legacy_margin = confidence_interval_95(legacy_test_accs)
    print(f"  TEST ACCURACY (Legacy): {legacy_mean:.3f} ± {legacy_margin:.3f}")

    # ═══════════════════════════════════════════════════════════
    # Evaluator C: Random Baseline (lower bound)
    # ═══════════════════════════════════════════════════════════
    random_acc = 1.0 / len(regimes)  # = 1/6 ≈ 0.167
    print(f"\n  RANDOM BASELINE: {random_acc:.3f} (1/{len(regimes)})")

    # ═══════════════════════════════════════════════════════════
    # FINAL VERDICT
    # ═══════════════════════════════════════════════════════════
    print("\n" + "=" * 72)
    print("  FINAL HONEST VERDICT")
    print("=" * 72)

    gap = abs(train_acc - mean_acc)
    overfitting = "YES ⚠️" if gap > 0.15 else "NO ✅"

    print(f"""
  ┌─────────────────────────────────────────────────────┐
  │ Bayesian Test Accuracy:  {mean_acc:.3f} ± {margin:.3f}          │
  │ Legacy Test Accuracy:    {legacy_mean:.3f} ± {legacy_margin:.3f}          │
  │ Random Baseline:         {random_acc:.3f}                  │
  │ Train/Test Gap:          {gap:.3f} (overfitting: {overfitting:7s}) │
  │                                                     │
  │ Bayesian vs Random:      {'+' if mean_acc > random_acc else '-'}{abs(mean_acc - random_acc):.3f}                  │
  │ Bayesian vs Legacy:      {'+' if mean_acc > legacy_mean else '-'}{abs(mean_acc - legacy_mean):.3f}                  │
  └─────────────────────────────────────────────────────┘
""")

    # Verdict
    if mean_acc > 0.80:
        print("  VERDICT: STRONG — System genuinely learns transferable patterns")
    elif mean_acc > 0.60:
        print("  VERDICT: MODERATE — Some learning, but significant room for improvement")
    elif mean_acc > random_acc + 0.10:
        print("  VERDICT: WEAK — Marginal improvement over random, learning is minimal")
    else:
        print("  VERDICT: FAILED — No meaningful learning detected")

    # Write results to text file
    out_path = str(BASE / "HONEST_BASELINE_RESULTS.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Morphosphere v38 — Honest Baseline Results\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Train seeds: {TRAIN_SEEDS}\n")
        f.write(f"Test seeds: {TEST_SEEDS}\n")
        f.write(f"Windows per seed: {TOTAL_WINDOWS}\n\n")
        f.write(f"Bayesian Test Accuracy: {mean_acc:.4f} ± {margin:.4f}\n")
        f.write(f"Legacy Test Accuracy: {legacy_mean:.4f} ± {legacy_margin:.4f}\n")
        f.write(f"Random Baseline: {random_acc:.4f}\n")
        f.write(f"Train/Test Gap: {gap:.4f}\n\n")
        f.write("Per-Regime Metrics (Bayesian):\n")
        for regime in regimes:
            m = regime_metrics[regime]
            f.write(f"  {regime}: P={m['precision']:.3f} R={m['recall']:.3f} "
                    f"F1={m['f1']:.3f} support={m['support']}\n")
        f.write(f"\nConfusion Matrix:\n")
        f.write("  " + "".join(f"{r[:6]:>7s}" for r in regimes) + "\n")
        for true_r in regimes:
            row = f"  {true_r[:8]:>8s}"
            for pred_r in regimes:
                row += f"{confusion[true_r][pred_r]:7d}"
            f.write(row + "\n")

    print(f"  Results saved to: {out_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
