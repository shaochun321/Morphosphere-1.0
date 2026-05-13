#!/usr/bin/env python3
"""Stdlib-only release verification for the v8.5.2 package."""
from __future__ import annotations
import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "v85_full_diagnostic_run.db"
REQUIRED = [
    ROOT / "run_smoke.py",
    ROOT / "run_v85_diagnostic.py",
    ROOT / "scripts" / "run_acceptance_sql.py",
    ROOT / "scripts" / "export_db_summary.py",
    ROOT / "migrations" / "011_mainline_manifest_crosswalk.sql",
    ROOT / "migrations" / "012_v852_execution_fidelity.sql",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run(args):
    return subprocess.run(args, cwd=str(ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def main() -> int:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        print("RELEASE VERIFY FAIL missing files:", missing)
        return 1
    smoke = run([sys.executable, "run_smoke.py"])
    print(smoke.stdout, end="")
    if smoke.returncode != 0:
        return smoke.returncode
    diag = run([sys.executable, "run_v85_diagnostic.py"])
    print(diag.stdout, end="")
    if diag.returncode != 0:
        return diag.returncode
    acceptance = run([sys.executable, "scripts/run_acceptance_sql.py", str(DB)])
    print(acceptance.stdout, end="")
    if acceptance.returncode != 0:
        return acceptance.returncode
    summary = run([sys.executable, "scripts/export_db_summary.py", str(DB), "reports/release_db_summary.json"])
    print(summary.stdout, end="")
    if summary.returncode != 0:
        return summary.returncode
    conn = sqlite3.connect(DB)
    mode = conn.execute("SELECT execution_mode FROM run_manifest").fetchone()[0]
    sci = conn.execute("SELECT COUNT(*) FROM run_manifest WHERE execution_mode='scientific_run'").fetchone()[0]
    conn.close()
    print(f"release_db_sha256={sha256(DB)}")
    print(f"execution_mode={mode}")
    print(f"scientific_run_rows={sci}")
    if mode != "diagnostic_full" or sci != 0:
        return 1
    print("RELEASE VERIFY PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
