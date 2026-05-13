#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acceptance checks for Morphosphere v0.7 Candidate Adoption Gate."""
from __future__ import annotations
import argparse, sqlite3, sys

REQUIRED_TABLES = [
    "candidate_adoption_run_manifest_v07",
    "candidate_profile_review_v07",
    "real_data_calibration_source_v07",
    "real_data_calibration_sample_v07",
    "real_data_calibration_mapping_v07",
    "real_data_calibration_result_v07",
    "candidate_adoption_gate_v07",
    "candidate_patch_manifest_v07",
    "source_fact_digest_v07",
    "shell0_lineage_audit_v07",
    "shell0_resolution_probe_v07",
    "shell0_adjudication_v07",
    "candidate_adoption_acceptance_report_v07",
    "candidate_adoption_artifact_manifest_v07",
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
        cur.execute(sql); row = cur.fetchone()
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
        ("manifest_single_run", count(cur, "candidate_adoption_run_manifest_v07") == 1),
        ("candidate_profile_review_single", count(cur, "candidate_profile_review_v07") == 1),
        ("candidate_improves_holdout", float(scalar(cur, "SELECT holdout_improvement FROM candidate_profile_review_v07", 0.0) or 0.0) > 0.01),
        ("patch_manifest_single", count(cur, "candidate_patch_manifest_v07") == 1),
        ("patch_not_auto_apply", count(cur, "candidate_patch_manifest_v07", "may_apply_automatically=0 AND requires_human_review=1") == 1),
        ("calibration_source_present", count(cur, "real_data_calibration_source_v07") == 1),
        ("calibration_samples_present", count(cur, "real_data_calibration_sample_v07") > 0),
        ("calibration_mappings_match_samples", count(cur, "real_data_calibration_mapping_v07") == count(cur, "real_data_calibration_sample_v07")),
        ("calibration_result_present", count(cur, "real_data_calibration_result_v07") == 1),
        ("calibration_fixture_blocks_auto", count(cur, "real_data_calibration_result_v07", "real_data_gate_status LIKE '%FIXTURE%' OR real_data_gate_status LIKE '%EXTERNAL%' ") == 1),
        ("gates_recorded", count(cur, "candidate_adoption_gate_v07") >= 8),
        ("shell0_lineage_audited", count(cur, "shell0_lineage_audit_v07") >= 5),
        ("shell0_probes_recorded", count(cur, "shell0_resolution_probe_v07") >= 6),
        ("shell0_adjudication_present", count(cur, "shell0_adjudication_v07") == 1),
        ("shell0_mixed_or_resolved", count(cur, "shell0_adjudication_v07", "final_verdict IN ('mixed_or_indeterminate','resolved','unresolved')") == 1),
        ("shell0_blocks_auto_when_unresolved", count(cur, "shell0_adjudication_v07", "final_verdict='mixed_or_indeterminate' AND blocks_auto_adoption=1") == 1),
        ("source_fact_digests_pass", count(cur, "source_fact_digest_v07", "status='FAIL'") == 0),
        ("final_decision_staged", count(cur, "candidate_adoption_run_manifest_v07", "final_decision='STAGED_PATCH_NOT_APPLIED' AND auto_adoption_allowed=0") == 1),
        ("p_r_before_xi_gate_present", count(cur, "candidate_adoption_gate_v07", "gate_name='p_r_before_xi_boundary' AND gate_status='PASS'") == 1),
        ("real_data_gate_blocks_or_passes", count(cur, "candidate_adoption_gate_v07", "gate_name='real_data_calibration_gate'") == 1),
        ("stored_acceptance_all_pass", count(cur, "candidate_adoption_acceptance_report_v07", "status='FAIL'") == 0),
        ("artifact_manifest_present", count(cur, "candidate_adoption_artifact_manifest_v07") >= 4),
    ])
    # Regression checks: old layers still present.
    legacy_tables = [
        "external_lab_run_manifest_v06", "device_edge_tick_state_v05", "matrix_foam_replay_result_v04",
        "full_replay_result_v03", "p_predictive_support_v022", "xi_boundary_guard_v022"
    ]
    for t in legacy_tables:
        checks.append((f"previous_layer_present_{t}", count(cur, t) > 0))
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    for name, ok in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}")
    print(f"SUMMARY {passed}/{total} PASS")
    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
