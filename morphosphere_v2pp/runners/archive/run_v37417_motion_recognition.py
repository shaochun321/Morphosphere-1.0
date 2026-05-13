#!/usr/bin/env python3
"""Motion Recognition Experiment: Long-window async->sync convergence test.

Generates 60 windows of structured motion with 6 regimes, tests whether
FHPMS+Hebbian memory can distinguish motion states and evolve from
async to near-sync recognition.
"""
from __future__ import annotations
import sqlite3, sys, json, time, uuid
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
REPORT_DIR = ROOT / "v37417_motion_recognition_reports"
REPORT_DIR.mkdir(exist_ok=True)
DB_PATH = ROOT / "v37417_motion_recognition.db"

from motion_recognition_engine import (
    run_motion_recognition_experiment, MOTION_REGIMES, MotionProcessGenerator)

def now(): return datetime.now(timezone.utc).isoformat()

# Extra tables for this experiment
EXTRA_TABLES = """
CREATE TABLE IF NOT EXISTS v37417_motion_recognition_log (
    record_id TEXT PRIMARY KEY, run_id TEXT, window_k INTEGER,
    true_regime TEXT, predicted_regime TEXT, correct INTEGER,
    confidence REAL, delay INTEGER, phase TEXT, displacement REAL,
    scores_json TEXT, memory_size INTEGER, created_at TEXT
);
CREATE TABLE IF NOT EXISTS v37417_motion_experiment_summary (
    summary_id TEXT PRIMARY KEY, run_id TEXT, total_windows INTEGER,
    overall_accuracy REAL, async_accuracy REAL, transition_accuracy REAL,
    sync_accuracy REAL, final_delay INTEGER, memory_entries INTEGER,
    regime_accuracy_json TEXT, sliding_accuracy_json TEXT, created_at TEXT
);
"""

def main():
    t0 = time.time()
    WINDOWS = 60; CELLS = 40
    print(f"=== Motion Recognition Experiment ===")
    print(f"Windows: {WINDOWS}, Cells: {CELLS}, Regimes: {len(MOTION_REGIMES)}")

    # Preview schedule
    gen = MotionProcessGenerator(total_windows=WINDOWS, n_cells=CELLS)
    print(f"\n  Regime schedule:")
    prev = None; start = 0
    for k, regime in enumerate(gen.schedule):
        if regime != prev:
            if prev: print(f"    win {start:2d}-{k-1:2d}: {prev}")
            prev = regime; start = k
    print(f"    win {start:2d}-{WINDOWS-1}: {prev}")

    if DB_PATH.exists(): DB_PATH.unlink()
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(EXTRA_TABLES)
    run_id = f"motion_exp_{uuid.uuid4().hex[:8]}"

    print(f"\n--- Running {WINDOWS}-window experiment ---")
    summary, results = run_motion_recognition_experiment(
        conn, run_id, total_windows=WINDOWS, n_cells=CELLS, seed=42)
    conn.commit()

    # Print detailed results
    print(f"\n{'='*80}")
    print("MOTION RECOGNITION RESULTS")
    print(f"{'='*80}")
    print(f"  Overall accuracy: {summary['overall_accuracy']*100:.1f}%")
    print(f"  Final delay: {summary['final_delay']} windows")
    print(f"  Memory entries: {summary['memory_entries']}")

    print(f"\n  Phase accuracy:")
    for phase in ["async", "transition", "sync"]:
        acc = summary["phase_accuracy"].get(phase, 0)
        print(f"    {phase:12s}: {acc*100:.1f}%")

    print(f"\n  Per-regime accuracy:")
    for regime, acc in sorted(summary["regime_accuracy"].items()):
        print(f"    {regime:15s}: {acc*100:.1f}%")

    # Window-by-window detail
    print(f"\n  Window-by-window (first 20 + last 10):")
    print(f"  {'Win':>4s} {'True':>12s} {'Predicted':>12s} {'OK':>3s} {'Conf':>5s} {'Delay':>5s} {'Phase':>10s}")
    for r in results[:20]:
        ok = "Y" if r["correct"] else "N"
        print(f"  {r['window']:4d} {r['true_regime']:>12s} {r['predicted']:>12s} {ok:>3s} {r['confidence']:5.2f} {r['delay']:5d} {r['phase']:>10s}")
    print(f"  {'...':>4s}")
    for r in results[-10:]:
        ok = "Y" if r["correct"] else "N"
        print(f"  {r['window']:4d} {r['true_regime']:>12s} {r['predicted']:>12s} {ok:>3s} {r['confidence']:5.2f} {r['delay']:5d} {r['phase']:>10s}")

    # Sliding accuracy curve
    print(f"\n  Sliding accuracy (window=5):")
    sa = summary["sliding_accuracy"]
    n = len(sa)
    for i in range(0, n, max(1, n // 12)):
        bar = "#" * int(sa[i] * 40)
        print(f"    win {i+2:2d}: {sa[i]*100:5.1f}% {bar}")

    # Delay evolution
    delays = summary["delay_evolution"]
    print(f"\n  Delay evolution:")
    for i in range(0, len(delays), max(1, len(delays) // 12)):
        print(f"    win {i+1:2d}: delay={delays[i]}")

    # Async -> sync convergence check
    early_acc = sum(1 for r in results[:15] if r["correct"]) / min(15, len(results))
    late_acc = sum(1 for r in results[-15:] if r["correct"]) / min(15, len(results))
    improvement = late_acc - early_acc

    print(f"\n  Async->Sync Convergence:")
    print(f"    Early accuracy (first 15 windows): {early_acc*100:.1f}%")
    print(f"    Late accuracy  (last 15 windows):  {late_acc*100:.1f}%")
    print(f"    Improvement: {improvement*100:+.1f}%")
    converged = improvement > 0.1 or late_acc > 0.7
    print(f"    Convergence: {'YES' if converged else 'NOT YET'}")

    elapsed = time.time() - t0
    report = {
        "version": "v37.4.17_motion", "elapsed_s": round(elapsed, 2),
        "summary": summary,
        "convergence": {
            "early_accuracy": round(early_acc, 3),
            "late_accuracy": round(late_acc, 3),
            "improvement": round(improvement, 3),
            "converged": converged,
        },
    }
    with open(REPORT_DIR / "motion_recognition_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Report: {REPORT_DIR}")
    print(f"  Elapsed: {elapsed:.1f}s")
    conn.close()

if __name__ == "__main__":
    main()
