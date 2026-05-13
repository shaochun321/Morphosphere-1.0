#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acceptance checks for Morphosphere v0.6 external lab."""
from __future__ import annotations
import argparse, json, sqlite3, sys
from pathlib import Path

REQUIRED_TABLES = [
    "external_lab_run_manifest_v06",
    "source_fact_digest_v06",
    "system_id_feature_matrix_v06",
    "system_id_parameter_profile_v06",
    "system_id_iteration_trace_v06",
    "active_inference_free_energy_trace_v06",
    "parameter_sensitivity_report_v06",
    "decision_note_v06",
    "adoption_guard_v06",
    "external_lab_acceptance_report_v06",
    "external_lab_artifact_manifest_v06",
]

def exists(cur, t):
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,))
    return cur.fetchone() is not None

def count(cur, t, where="1=1"):
    if not exists(cur, t): return 0
    cur.execute(f"SELECT COUNT(*) FROM {t} WHERE {where}")
    return int(cur.fetchone()[0])

def scalar(cur, sql, default=None):
    try:
        cur.execute(sql); row=cur.fetchone()
        return default if row is None else row[0]
    except Exception:
        return default

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    checks = []
    cur.execute("PRAGMA integrity_check")
    checks.append(("sqlite_integrity_ok", cur.fetchone()[0] == "ok"))
    for t in REQUIRED_TABLES:
        checks.append((f"table_exists_{t}", exists(cur, t)))
    checks.extend([
        ("manifest_single_run", count(cur, "external_lab_run_manifest_v06") == 1),
        ("feature_rows_nonzero", count(cur, "system_id_feature_matrix_v06") > 0),
        ("train_and_holdout_present", count(cur, "system_id_feature_matrix_v06", "split='train'") > 0 and count(cur, "system_id_feature_matrix_v06", "split='holdout'") > 0),
        ("profiles_recorded", count(cur, "system_id_parameter_profile_v06") >= 2),
        ("candidate_not_adopted", count(cur, "system_id_parameter_profile_v06", "adoption_status='candidate_not_adopted'") == 1),
        ("decision_requires_human_review", count(cur, "decision_note_v06", "may_update_mainline=0 AND requires_human_review=1") >= 1),
        ("source_digests_pass", count(cur, "source_fact_digest_v06", "status='FAIL'") == 0),
        ("guards_active", count(cur, "adoption_guard_v06", "status='active'") >= 6),
        ("p_r_before_xi_guard", count(cur, "adoption_guard_v06", "guard_name='p_r_before_xi' AND status='active'") == 1),
        ("free_energy_rows_match_features", count(cur, "active_inference_free_energy_trace_v06") == count(cur, "system_id_feature_matrix_v06")),
        ("sensitivity_rows_match_features", count(cur, "parameter_sensitivity_report_v06") >= 10),
        ("internal_acceptance_all_pass", count(cur, "external_lab_acceptance_report_v06", "status='FAIL'") == 0),
    ])
    cur.execute("SELECT baseline_train_loss, fitted_train_loss, baseline_holdout_loss, fitted_holdout_loss FROM external_lab_run_manifest_v06 LIMIT 1")
    row = cur.fetchone()
    if row:
        btr, ftr, bho, fho = map(float, row)
        checks.append(("fitted_train_loss_below_baseline", ftr < btr))
        checks.append(("fitted_holdout_loss_reasonable", fho <= bho + 0.02))
    else:
        checks.append(("loss_metrics_present", False))
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"SUMMARY {passed}/{total} PASS")
    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
