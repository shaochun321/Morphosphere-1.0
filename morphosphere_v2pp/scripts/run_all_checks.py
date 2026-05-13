#!/usr/bin/env python3
"""Morphosphere v37.4.92 — One-shot Full Verification Suite.

Runs both test pipelines sequentially and reports combined results.
Exit code 0 = all pass, 1 = any failure.

Usage:
    python scripts/run_all_checks.py
"""
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # morphosphere_v2pp/

SUITES = [
    {
        "name": "A/B/C Stress Benchmark",
        "script": ROOT / "runners" / "run_v37450_ab_test.py",
        "expected_pattern": "ALL PASS",
    },
    {
        "name": "Integrated Pipeline",
        "script": ROOT / "runners" / "run_v37460_integrated.py",
        "expected_pattern": "checks passed",
    },
]


def run_suite(suite: dict) -> bool:
    """Run a test suite and return True if it passed."""
    print(f"\n{'='*70}")
    print(f"  Running: {suite['name']}")
    print(f"  Script:  {suite['script'].name}")
    print(f"{'='*70}")
    t0 = time.time()

    result = subprocess.run(
        [sys.executable, str(suite["script"])],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )

    elapsed = time.time() - t0
    output = result.stdout + result.stderr

    # Print last 30 lines
    lines = output.strip().split("\n")
    for line in lines[-30:]:
        print(f"  {line}")

    passed = suite["expected_pattern"] in output and result.returncode == 0
    status = "PASS" if passed else "FAIL"
    print(f"\n  [{status}] {suite['name']} ({elapsed:.1f}s)")
    return passed


def main():
    print(f"{'#'*70}")
    print(f"  Morphosphere v37.4.91 — Full Verification Suite")
    print(f"{'#'*70}")
    t0 = time.time()

    results = []
    for suite in SUITES:
        try:
            ok = run_suite(suite)
        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] {suite['name']}")
            ok = False
        except Exception as e:
            print(f"  [ERROR] {suite['name']}: {e}")
            ok = False
        results.append((suite["name"], ok))

    elapsed = time.time() - t0
    total = len(results)
    passed = sum(1 for _, ok in results if ok)

    print(f"\n{'#'*70}")
    print(f"  SUMMARY")
    print(f"{'#'*70}")
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"\n  Total: {passed}/{total} suites passed ({elapsed:.1f}s)")
    print(f"{'#'*70}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
