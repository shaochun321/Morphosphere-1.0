#!/usr/bin/env python3
"""Run Morphosphere v8.5.3 validation perturbations.

Loads the v8.5 diagnostic DB (or creates a minimal test DB),
runs the PerturbationExecutor masking suite against all PR_candidate
hypotheses, and reports results.

Usage:
    py -3 run_v853_validation.py [--db PATH]
"""
from __future__ import annotations
import argparse, os, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
DB_DEFAULT = ROOT / "v85_full_diagnostic_run.db"


def main() -> int:
    parser = argparse.ArgumentParser(description="v8.5.3 perturbation validation")
    parser.add_argument("--db", default=str(DB_DEFAULT), help="SQLite DB path")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] DB not found: {db_path}")
        print("  Run 'py -3 run_v85_diagnostic.py' first to create the diagnostic DB.")
        return 1

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure new-format columns exist (migration from old schema)
    existing_cols = {r[1] for r in conn.execute(
        "PRAGMA table_info(masking_counterevidence_record)").fetchall()}
    for col, ctype, default in [
        ("baseline_score", "REAL", "0.0"),
        ("perturbed_score", "REAL", "0.0"),
        ("details", "TEXT", "''"),
    ]:
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE masking_counterevidence_record "
                         f"ADD COLUMN {col} {ctype} DEFAULT {default}")
    conn.commit()

    # Check for required tables
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    required = {"object_hypothesis", "occupancy_measure", "spacetime_cell",
                "information_fiber", "masking_counterevidence_record"}
    missing = required - tables
    if missing:
        print(f"[ERROR] Missing tables: {missing}")
        return 1

    from morphosphere.active_exec.perturbations.executor import PerturbationExecutor

    # Find hypotheses to test
    hyps = conn.execute(
        "SELECT hypothesis_id, hypothesis_type, status, run_id "
        "FROM object_hypothesis WHERE status IN ('candidate','PR_candidate','mask_supported') "
        "ORDER BY stage_k DESC LIMIT 5"
    ).fetchall()

    if not hyps:
        print("[WARN] No candidate hypotheses found in DB.")
        return 0

    run_id = hyps[0][3]
    executor = PerturbationExecutor(conn, run_id=run_id, seed=853)

    print("=" * 65)
    print("  Morphosphere v8.5.3 Perturbation Validation")
    print("=" * 65)
    print(f"  DB: {db_path}")
    print(f"  Run ID: {run_id}")
    print(f"  Hypotheses to test: {len(hyps)}\n")

    total_pass = total_fail = 0
    for hid, htype, status, _ in hyps:
        print(f"  --- {hid} ({htype}, {status}) ---")
        results = executor.run_masking_suite(hid)
        conn.commit()

        for r in results["individual_results"]:
            print(f"    {r['masking_type']:28s} ret={r['retention']:.3f} → {r['verdict']}")

        agg = results["aggregate_verdict"]
        ok = agg in ("supports_confirmation", "weakens_confirmation")
        print(f"    Aggregate: {agg} {'[OK]' if ok else '[CHECK]'}")
        if ok:
            total_pass += 1
        else:
            total_fail += 1
        print()

    # Summary
    mcr = conn.execute("SELECT COUNT(*) FROM masking_counterevidence_record").fetchone()[0]
    print(f"{'=' * 65}")
    print(f"  Total masking_counterevidence_record: {mcr}")
    print(f"  Results: {total_pass} passed, {total_fail} flagged out of {len(hyps)}")
    print(f"{'=' * 65}")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
