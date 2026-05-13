#!/usr/bin/env python3
"""Minimal deployment smoke test for the v8.5.3 diagnostic validation package."""
from pathlib import Path
required = [
    "run_v85_diagnostic.py",
    "run_v853_validation.py",
    "scripts/run_acceptance_sql.py",
    "scripts/run_v853_behavioral_acceptance.py",
    "migrations/012_v852_execution_fidelity.sql",
    "migrations/013_v853_validation_perturbation.sql",
    "configs/v853_validation.json",
    "src/morphosphere/cli.py",
]
root = Path(__file__).resolve().parent
missing = [p for p in required if not (root / p).exists()]
if missing:
    print("SMOKE FAIL missing:", missing)
    raise SystemExit(1)
print("SMOKE PASS required v8.5.2 and v8.5.3 entrypoints, configs, and migrations present")
