#!/usr/bin/env python3
"""Full local verification for Morphosphere v8.5.3 physical-freeze hardening release."""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "-S", "run_smoke.py"],
    [sys.executable, "-S", "run_v85_diagnostic.py", "--calibration_profile", "basic_physics_v1", "--execution_mode", "diagnostic_full", "--scientific_use_allowed", "false"],
    [sys.executable, "-S", "scripts/run_acceptance_sql.py", "v85_full_diagnostic_run.db"],
    [sys.executable, "-S", "run_v853_validation.py", "--db", "v85_full_diagnostic_run.db", "--config", "configs/v853_validation.json"],
    [sys.executable, "-S", "run_v853_validation.py", "--db", "v85_full_diagnostic_run.db", "--config", "configs/v853_validation.json"],
    [sys.executable, "-S", "scripts/export_v853_artifact_manifest.py", "v85_full_diagnostic_run.db"],
    [sys.executable, "-S", "scripts/run_v853_behavioral_acceptance.py", "v85_full_diagnostic_run.db"],
    [sys.executable, "-S", "scripts/export_db_summary.py", "v85_full_diagnostic_run.db", "reports/release_db_summary.json"],
]


def main() -> int:
    logs = ROOT / "reports"
    logs.mkdir(exist_ok=True)
    for i, cmd in enumerate(COMMANDS, 1):
        print("RUN", " ".join(cmd))
        proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
        (logs / f"v853_hardening_verify_{i}.log").write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr)
            print(f"HARDENING RELEASE VERIFY FAIL at step {i}: {' '.join(cmd)}")
            return proc.returncode
    print("V8.5.3 PHYSICAL-FREEZE HARDENING RELEASE VERIFY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
