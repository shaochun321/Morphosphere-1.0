#!/usr/bin/env python3
"""Honest Motion Recognition Evaluation.

Step 1: Independent train/test split — no data leakage
Step 2: A/B comparison — Legacy lookup vs Bayesian classifier
Step 3: Statistical reporting — mean ± std, confusion matrix, per-regime
"""
from __future__ import annotations
import json, time, math, copy
from pathlib import Path
from collections import defaultdict

from motion_recognition_engine import (
    MotionProcessGenerator, FeatureExtractor, BayesianMotionRecognizer,
    LegacyLookupRecognizer, MOTION_REGIMES, FEATURE_NAMES)

REPORT_DIR = Path(__file__).resolve().parent / "v37417_honest_evaluation_reports"
REPORT_DIR.mkdir(exist_ok=True)

# ════════════════════════════════════════════
# Strict train/test seed separation
# ════════════════════════════════════════════
TRAIN_SEEDS = [42, 100, 200]      # 3 runs for training
TEST_SEEDS  = [500, 600, 700]     # 3 completely independent runs for testing
# NO OVERLAP between train and test seeds.


def run_one_pass(gen_seed, extractor_factory, recognizer, learn=True):
    """Run one 60-window pass. Returns list of per-window results."""
    gen = MotionProcessGenerator(total_windows=60, n_cells=40, seed=gen_seed)
    ext = extractor_factory()
    prev_pos = None
    results = []
    for k in range(60):
        state, positions, displacements = gen.step(k)
        if prev_pos is not None:
            fvec = ext.extract(prev_pos, positions, displacements)
            predicted, confidence, scores = recognizer.classify(fvec)
            correct = (predicted == state.regime)
            if learn:
                recognizer.learn(fvec, state.regime)
            recognizer.update_recognition_delay(k, correct)
            results.append({
                "window": k, "true": state.regime,
                "pred": predicted, "correct": correct,
                "confidence": round(confidence, 3),
            })
        prev_pos = dict(positions)
    return results


def compute_metrics(all_results):
    """Compute accuracy, per-regime accuracy, confusion matrix."""
    total = len(all_results)
    correct = sum(1 for r in all_results if r["correct"])
    acc = correct / max(total, 1)

    # Per-regime
    regime_acc = {}
    for regime in MOTION_REGIMES:
        matches = [r for r in all_results if r["true"] == regime]
        if matches:
            regime_acc[regime] = sum(1 for m in matches if m["correct"]) / len(matches)

    # Confusion matrix
    matrix = defaultdict(lambda: defaultdict(int))
    for r in all_results:
        matrix[r["true"]][r["pred"]] += 1

    return {
        "accuracy": round(acc, 4),
        "n_samples": total,
        "per_regime": {r: round(a, 3) for r, a in regime_acc.items()},
        "confusion": {k: dict(v) for k, v in matrix.items()},
    }


def main():
    t0 = time.time()
    print("=" * 80)
    print("HONEST MOTION RECOGNITION EVALUATION")
    print("=" * 80)
    print(f"  Train seeds: {TRAIN_SEEDS}")
    print(f"  Test seeds:  {TEST_SEEDS} (completely independent)")
    print(f"  Regimes: {len(MOTION_REGIMES)}")
    print(f"  Features: {len(FEATURE_NAMES)} dimensions")

    # ════════════════════════════════════════
    # Test both recognizers
    # ════════════════════════════════════════
    recognizers = {
        "Legacy (lookup table)": lambda: LegacyLookupRecognizer(),
        "Bayesian (online)":     lambda: BayesianMotionRecognizer(prior_var=1.0),
    }

    all_reports = {}

    for rec_name, rec_factory in recognizers.items():
        print(f"\n{'─'*60}")
        print(f"  Recognizer: {rec_name}")
        print(f"{'─'*60}")

        recognizer = rec_factory()

        # ── Phase 1: TRAIN (learn on training seeds) ──
        print(f"  Training on seeds {TRAIN_SEEDS}...")
        train_results_all = []
        for seed in TRAIN_SEEDS:
            results = run_one_pass(seed, FeatureExtractor, recognizer, learn=True)
            train_results_all.extend(results)
            train_acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
            print(f"    seed={seed}: {train_acc*100:.1f}%")

        train_metrics = compute_metrics(train_results_all)
        print(f"  Train accuracy: {train_metrics['accuracy']*100:.1f}%")

        # ── Phase 2: TEST (NO learning, completely new data) ──
        print(f"  Testing on seeds {TEST_SEEDS} (NO learning)...")
        test_results_all = []
        test_per_seed = []
        for seed in TEST_SEEDS:
            results = run_one_pass(seed, FeatureExtractor, recognizer, learn=False)
            test_results_all.extend(results)
            seed_acc = sum(1 for r in results if r["correct"]) / max(len(results), 1)
            test_per_seed.append(seed_acc)
            print(f"    seed={seed}: {seed_acc*100:.1f}%")

        test_metrics = compute_metrics(test_results_all)

        # Statistical summary
        mean_acc = sum(test_per_seed) / len(test_per_seed)
        std_acc = math.sqrt(sum((a - mean_acc)**2 for a in test_per_seed) / max(len(test_per_seed) - 1, 1))

        print(f"\n  TEST RESULTS:")
        print(f"    Accuracy: {mean_acc*100:.1f}% ± {std_acc*100:.1f}%")
        print(f"    Train-Test gap: {(train_metrics['accuracy'] - mean_acc)*100:+.1f}%")

        # Per-regime on test
        print(f"    Per-regime (test):")
        for regime in sorted(MOTION_REGIMES.keys()):
            acc = test_metrics["per_regime"].get(regime, 0)
            bar = "#" * int(acc * 30)
            print(f"      {regime:15s}: {acc*100:5.1f}% {bar}")

        # Confusion matrix
        regimes = sorted(MOTION_REGIMES.keys())
        tp_label = "True / Pred"
        print(f"\n    Confusion (test):")
        header = f"    {tp_label:>15s}" + "".join(f" {r[:6]:>6s}" for r in regimes)
        print(header)
        for true_r in regimes:
            row = f"    {true_r:>15s}"
            for pred_r in regimes:
                cnt = test_metrics["confusion"].get(true_r, {}).get(pred_r, 0)
                row += f" {cnt:6d}" if cnt > 0 else "      ."
                
            print(row)

        # Overfit check
        gap = train_metrics["accuracy"] - mean_acc
        if gap > 0.15:
            verdict = "OVERFITTING (train >> test)"
        elif gap > 0.05:
            verdict = "MILD OVERFIT"
        elif mean_acc >= 0.75:
            verdict = "GOOD GENERALIZATION"
        else:
            verdict = "UNDERFITTING"
        print(f"    Verdict: {verdict}")

        # Show Bayesian params if applicable
        if hasattr(recognizer, 'get_params_summary'):
            print(f"\n    Learned distributions:")
            params = recognizer.get_params_summary()
            print(f"    {'Regime':>15s}  {'n':>4s}  {'Features: ' + ' '.join(f'{fn[:6]:>7s}' for fn in FEATURE_NAMES)}")
            for regime in regimes:
                if regime in params:
                    p = params[regime]
                    mu_str = " ".join(f"{m:7.4f}" for m in p["mu"])
                    print(f"    {regime:>15s}  {p['n']:4d}  {mu_str}")

        all_reports[rec_name] = {
            "train_accuracy": train_metrics["accuracy"],
            "test_accuracy": round(mean_acc, 4),
            "test_std": round(std_acc, 4),
            "test_per_seed": [round(a, 4) for a in test_per_seed],
            "train_test_gap": round(gap, 4),
            "test_per_regime": test_metrics["per_regime"],
            "test_confusion": test_metrics["confusion"],
            "verdict": verdict,
        }

    # ════════════════════════════════════════
    # Final comparison
    # ════════════════════════════════════════
    print(f"\n{'='*80}")
    print("FINAL COMPARISON")
    print(f"{'='*80}")
    print(f"  {'Recognizer':>25s}  {'Train':>7s}  {'Test':>12s}  {'Gap':>6s}  {'Verdict':>20s}")
    for name, rep in all_reports.items():
        print(f"  {name:>25s}  {rep['train_accuracy']*100:6.1f}%  "
              f"{rep['test_accuracy']*100:5.1f}±{rep['test_std']*100:.1f}%  "
              f"{rep['train_test_gap']*100:+5.1f}%  {rep['verdict']:>20s}")

    elapsed = time.time() - t0
    report = {"version": "v37417_honest_eval", "elapsed_s": round(elapsed, 2),
              "train_seeds": TRAIN_SEEDS, "test_seeds": TEST_SEEDS, "results": all_reports}
    with open(REPORT_DIR / "honest_evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ════════════════════════════════════════
    # Write to SQLite database
    # ════════════════════════════════════════
    import sqlite3, uuid
    from datetime import datetime, timezone
    DB_PATH = Path(__file__).resolve().parent / "v37417_honest_evaluation.db"
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS v37417_eval_config (
        config_id TEXT PRIMARY KEY, train_seeds TEXT, test_seeds TEXT,
        n_regimes INTEGER, n_features INTEGER, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_eval_comparison (
        comparison_id TEXT PRIMARY KEY, recognizer_name TEXT,
        train_accuracy REAL, test_accuracy REAL, test_std REAL,
        train_test_gap REAL, verdict TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_eval_per_regime (
        record_id TEXT PRIMARY KEY, recognizer_name TEXT, regime TEXT,
        test_accuracy REAL, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_eval_confusion (
        record_id TEXT PRIMARY KEY, recognizer_name TEXT,
        true_regime TEXT, predicted_regime TEXT, count INTEGER, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_eval_bayesian_params (
        param_id TEXT PRIMARY KEY, regime TEXT, n_observations INTEGER,
        feature_name TEXT, feature_index INTEGER,
        mu REAL, std REAL, variance REAL, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS v37417_eval_window_results (
        result_id TEXT PRIMARY KEY, recognizer_name TEXT, seed INTEGER,
        phase TEXT, window_k INTEGER, true_regime TEXT, predicted_regime TEXT,
        correct INTEGER, confidence REAL, created_at TEXT
    );
    """)
    now_ts = datetime.now(timezone.utc).isoformat()
    uid = lambda p: f"{p}_{uuid.uuid4().hex[:8]}"

    conn.execute("INSERT INTO v37417_eval_config VALUES (?,?,?,?,?,?)",
                 (uid("cfg"), json.dumps(TRAIN_SEEDS), json.dumps(TEST_SEEDS),
                  len(MOTION_REGIMES), len(FEATURE_NAMES), now_ts))

    for rec_name, rep in all_reports.items():
        conn.execute("INSERT INTO v37417_eval_comparison VALUES (?,?,?,?,?,?,?,?)",
                     (uid("cmp"), rec_name, rep["train_accuracy"],
                      rep["test_accuracy"], rep["test_std"],
                      rep["train_test_gap"], rep["verdict"], now_ts))
        for regime, acc in rep["test_per_regime"].items():
            conn.execute("INSERT INTO v37417_eval_per_regime VALUES (?,?,?,?,?)",
                         (uid("pr"), rec_name, regime, acc, now_ts))
        for true_r, preds in rep["test_confusion"].items():
            for pred_r, cnt in preds.items():
                conn.execute("INSERT INTO v37417_eval_confusion VALUES (?,?,?,?,?,?)",
                             (uid("cf"), rec_name, true_r, pred_r, cnt, now_ts))

    # Write per-window results (re-run to capture)
    for rec_name_key, rec_factory in recognizers.items():
        recognizer2 = rec_factory()
        for seed in TRAIN_SEEDS:
            results2 = run_one_pass(seed, FeatureExtractor, recognizer2, learn=True)
            for r in results2:
                conn.execute("INSERT INTO v37417_eval_window_results VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (uid("wr"), rec_name_key, seed, "train", r["window"],
                     r["true"], r["pred"], 1 if r["correct"] else 0, r["confidence"], now_ts))
        for seed in TEST_SEEDS:
            results2 = run_one_pass(seed, FeatureExtractor, recognizer2, learn=False)
            for r in results2:
                conn.execute("INSERT INTO v37417_eval_window_results VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (uid("wr"), rec_name_key, seed, "test", r["window"],
                     r["true"], r["pred"], 1 if r["correct"] else 0, r["confidence"], now_ts))

    # Write Bayesian learned parameters
    bayes_rec = BayesianMotionRecognizer(prior_var=1.0)
    for seed in TRAIN_SEEDS:
        run_one_pass(seed, FeatureExtractor, bayes_rec, learn=True)
    params = bayes_rec.get_params_summary()
    for regime, p in params.items():
        for fi, fn in enumerate(FEATURE_NAMES):
            conn.execute("INSERT INTO v37417_eval_bayesian_params VALUES (?,?,?,?,?,?,?,?,?)",
                         (uid("bp"), regime, p["n"], fn, fi,
                          p["mu"][fi], p["std"][fi], p["std"][fi]**2, now_ts))

    conn.commit()
    db_size = DB_PATH.stat().st_size // 1024
    total_rows = sum(conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
                     for t in ["v37417_eval_config", "v37417_eval_comparison",
                               "v37417_eval_per_regime", "v37417_eval_confusion",
                               "v37417_eval_bayesian_params", "v37417_eval_window_results"])
    conn.close()
    print(f"\n  Database: {DB_PATH.name} ({db_size} KB, {total_rows} rows)")
    print(f"    Tables: eval_config, eval_comparison, eval_per_regime,")
    print(f"            eval_confusion, eval_bayesian_params, eval_window_results")
    print(f"\n  Report: {REPORT_DIR}")
    print(f"  Elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
