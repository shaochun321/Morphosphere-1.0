#!/usr/bin/env python3
"""Run Morphosphere v8.5.3 behavioral + hardening acceptance SQL."""
from __future__ import annotations
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "v85_full_diagnostic_run.db"

CHECKS = [
    ("integrity_check", "PRAGMA integrity_check", lambda r: r and r[0][0] == "ok"),
    ("v853_manifest_present", "SELECT COUNT(*) FROM perturbation_run_manifest WHERE validation_version='v8.5.3' AND execution_mode='diagnostic_full'", lambda r: r[0][0] > 0),
    ("not_scientific_run", "SELECT COUNT(*) FROM perturbation_run_manifest WHERE execution_mode='scientific_run' OR forbidden_use NOT LIKE '%scientific_run%'", lambda r: r[0][0] == 0),
    ("six_perturbations_recorded", "SELECT COUNT(DISTINCT perturbation_type) FROM perturbation_effect_report", lambda r: r[0][0] >= 6),
    ("all_effects_passed", "SELECT COUNT(*) FROM perturbation_effect_report WHERE passed=0", lambda r: r[0][0] == 0),
    ("counterfactual_acceptance_passed", "SELECT COUNT(*) FROM counterfactual_acceptance_report WHERE passed=0", lambda r: r[0][0] == 0),
    ("failed_expectations_visible_and_empty_when_passed", "SELECT (SELECT COUNT(*) FROM failed_expectation_report), (SELECT COUNT(*) FROM perturbation_effect_report WHERE passed=0)", lambda r: r and r[0][0] == r[0][1]),
    ("signal_shuffle_entropy_increases", "SELECT delta_value FROM perturbation_effect_report WHERE perturbation_type='signal_shuffle' ORDER BY created_at DESC LIMIT 1", lambda r: r and r[0][0] > 0),
    ("geometry_shift_cost_increases", "SELECT delta_value FROM perturbation_effect_report WHERE perturbation_type='geometry_shift' ORDER BY created_at DESC LIMIT 1", lambda r: r and r[0][0] > 0),
    ("boundary_flip_rejection_increases", "SELECT delta_value FROM perturbation_effect_report WHERE perturbation_type='boundary_flip' ORDER BY created_at DESC LIMIT 1", lambda r: r and r[0][0] > 0),
    ("masking_injection_o_support_decreases", "SELECT delta_value FROM perturbation_effect_report WHERE perturbation_type='masking_injection' ORDER BY created_at DESC LIMIT 1", lambda r: r and r[0][0] < 0),
    ("xi_pressure_increases", "SELECT delta_value FROM perturbation_effect_report WHERE perturbation_type='xi_pressure_injection' ORDER BY created_at DESC LIMIT 1", lambda r: r and r[0][0] > 0),
    ("threshold_sweep_nonflat", "SELECT COUNT(*), MAX(metric_value)-MIN(metric_value) FROM threshold_sweep_record", lambda r: r and r[0][0] > 0 and r[0][1] > 0),
    ("transport_cost_matrix_exported", "SELECT COUNT(*) FROM transport_cost_matrix_report", lambda r: r[0][0] > 0),
    ("transport_cost_matrix_record_exported", "SELECT COUNT(*) FROM transport_cost_matrix_record", lambda r: r[0][0] > 0),
    ("object_evidence_terms_exported", "SELECT COUNT(*) FROM object_evidence_record WHERE evidence_terms_json NOT IN ('[]','') AND evidence_terms_json LIKE '%xi_pressure_penalty%'", lambda r: r[0][0] > 0),
    ("xi_residual_mass_exported", "SELECT COUNT(*) FROM xi_residual_mass_report WHERE perturbed_residue_mass > baseline_residue_mass", lambda r: r[0][0] > 0),
    ("xi_residue_mass_record_exported", "SELECT COUNT(*) FROM xi_residue_mass_record WHERE residue_mass > 0 AND current_state != 'unknown'", lambda r: r[0][0] > 0),
    ("reproducibility_report_present", "SELECT COUNT(*) FROM v853_reproducibility_report", lambda r: r[0][0] > 0),
    ("reproducibility_latest_compared_and_passed", "SELECT compared_metric_count, max_abs_delta, tolerance, passed FROM v853_reproducibility_report ORDER BY created_at DESC LIMIT 1", lambda r: bool(r) and r[0][0] > 0 and r[0][1] <= r[0][2] and r[0][3] == 1),
    ("artifact_manifest_exported", "SELECT COUNT(*) FROM v853_release_artifact_manifest WHERE release_version='v8.5.3-hardening'", lambda r: r[0][0] >= 5),
]


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 2
    conn = sqlite3.connect(DB)
    failed = []
    print(f"DB: {DB}")
    for name, sql, pred in CHECKS:
        try:
            rows = conn.execute(sql).fetchall()
            ok = pred(rows)
        except Exception as e:
            rows = [[f"ERROR: {e}"]]
            ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {rows}")
        if not ok:
            failed.append(name)
    conn.close()
    print(json.dumps({"passed": len(CHECKS) - len(failed), "total": len(CHECKS), "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
