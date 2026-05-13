#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Acceptance checks for shell0 boundary closure v0.8."""
from __future__ import annotations
import argparse
import sqlite3
import sys

REQUIRED_TABLES = [
    "shell0_closure_run_manifest_v08",
    "source_fact_digest_v08",
    "shell0_boundary_evidence_v08",
    "shell0_multiresolution_probe_v08",
    "shell0_contact_ablation_trial_v08",
    "shell0_ghost_shell_control_v08",
    "shell0_closure_adjudication_v08",
    "external_real_data_trial_source_v08",
    "external_real_data_trial_sample_v08",
    "external_real_data_trial_mapping_v08",
    "external_real_data_trial_result_v08",
    "candidate_adoption_gate_v08",
    "candidate_patch_review_v08",
    "shell0_closure_acceptance_report_v08",
    "shell0_closure_artifact_manifest_v08",
]
SOURCE_FACT_TABLES = [
    "spacetime_cell", "information_fiber", "raw_event_stream",
    "cell_spatial_coordinate_snapshot", "information_relative_coordinate_snapshot",
    "system_clock_entry", "p_predictive_support_v022", "r_counterstructure_v022",
    "xi_boundary_guard_v022", "substrate_stress_tensor_v04",
    "cell_matrix_contact_v04", "foam_edge_state_v04", "mechanotransduction_event_v04",
    "preneural_synaptic_edge_v05", "device_edge_tick_state_v05",
]

def scalar(cur, sql, default=None):
    try:
        row = cur.execute(sql).fetchone()
        if row is None or row[0] is None:
            return default
        return row[0]
    except Exception:
        return default

def exists(cur, table):
    return cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

def count(cur, table, where="1=1"):
    if not exists(cur, table):
        return 0
    return int(cur.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    cur = con.cursor()
    checks = []
    def add(name, ok, obs, exp):
        checks.append((name, bool(ok), obs, exp))
    add("sqlite_openable", scalar(cur, "SELECT COUNT(*) FROM sqlite_master") is not None, "open", "open")
    for t in REQUIRED_TABLES:
        add(f"table_exists:{t}", exists(cur, t), "exists" if exists(cur, t) else "missing", "exists")
    add("manifest_one_row", count(cur, "shell0_closure_run_manifest_v08") == 1, count(cur, "shell0_closure_run_manifest_v08"), "1")
    add("shell0_adjudication_one_row", count(cur, "shell0_closure_adjudication_v08") == 1, count(cur, "shell0_closure_adjudication_v08"), "1")
    final_verdict = scalar(cur, "SELECT final_verdict FROM shell0_closure_adjudication_v08 LIMIT 1", "")
    add("shell0_closed_structural", str(final_verdict).startswith("closed_as_structural"), final_verdict, "closed_as_structural*")
    add("shell0_not_auto_blocking", scalar(cur, "SELECT blocks_auto_adoption FROM shell0_closure_adjudication_v08 LIMIT 1", 1) == 0, scalar(cur, "SELECT blocks_auto_adoption FROM shell0_closure_adjudication_v08 LIMIT 1", 1), "0")
    add("physical_watchlist_active", scalar(cur, "SELECT physical_watchlist FROM shell0_closure_adjudication_v08 LIMIT 1", 0) == 1, scalar(cur, "SELECT physical_watchlist FROM shell0_closure_adjudication_v08 LIMIT 1", 0), "1")
    add("multiresolution_complete", count(cur, "shell0_multiresolution_probe_v08") >= 4, count(cur, "shell0_multiresolution_probe_v08"), ">=4")
    add("ghost_controls_complete", count(cur, "shell0_ghost_shell_control_v08") >= 5, count(cur, "shell0_ghost_shell_control_v08"), ">=5")
    add("ablation_trials_complete", count(cur, "shell0_contact_ablation_trial_v08") >= 6, count(cur, "shell0_contact_ablation_trial_v08"), ">=6")
    add("external_source_present", count(cur, "external_real_data_trial_source_v08") == 1, count(cur, "external_real_data_trial_source_v08"), "1")
    add("external_samples_present", count(cur, "external_real_data_trial_sample_v08") > 0, count(cur, "external_real_data_trial_sample_v08"), ">0")
    add("external_mappings_match", count(cur, "external_real_data_trial_mapping_v08") == count(cur, "external_real_data_trial_sample_v08"), count(cur, "external_real_data_trial_mapping_v08"), "sample_count")
    add("external_result_one", count(cur, "external_real_data_trial_result_v08") == 1, count(cur, "external_real_data_trial_result_v08"), "1")
    gate = scalar(cur, "SELECT real_data_gate_status FROM external_real_data_trial_result_v08 LIMIT 1", "")
    add("external_gate_valid", gate in {"BLOCKED_FIXTURE_ONLY", "BLOCKED_SCHEMA_INVALID", "BLOCKED_LOW_ALIGNMENT", "REAL_DATA_TRIAL_PASSED_REVIEW_REQUIRED"}, gate, "known gate")
    add("candidate_patch_not_auto_applied", scalar(cur, "SELECT auto_adoption_allowed FROM shell0_closure_run_manifest_v08 LIMIT 1", 1) == 0, scalar(cur, "SELECT auto_adoption_allowed FROM shell0_closure_run_manifest_v08 LIMIT 1", 1), "0")
    add("manual_review_required", scalar(cur, "SELECT manual_review_required FROM shell0_closure_run_manifest_v08 LIMIT 1", 0) == 1, scalar(cur, "SELECT manual_review_required FROM shell0_closure_run_manifest_v08 LIMIT 1", 0), "1")
    add("source_fact_digest_rows", count(cur, "source_fact_digest_v08") == len(SOURCE_FACT_TABLES), count(cur, "source_fact_digest_v08"), str(len(SOURCE_FACT_TABLES)))
    add("source_facts_unchanged", count(cur, "source_fact_digest_v08", "unchanged=1") == len(SOURCE_FACT_TABLES), count(cur, "source_fact_digest_v08", "unchanged=1"), str(len(SOURCE_FACT_TABLES)))
    add("stored_acceptance_all_pass", count(cur, "shell0_closure_acceptance_report_v08", "passed=0") == 0, count(cur, "shell0_closure_acceptance_report_v08", "passed=0"), "0")
    add("artifact_manifest_present", count(cur, "shell0_closure_artifact_manifest_v08") >= 2, count(cur, "shell0_closure_artifact_manifest_v08"), ">=2")
    # mainline preservation checks
    add("spacetime_cell_count", count(cur, "spacetime_cell") == 500, count(cur, "spacetime_cell"), "500")
    add("information_fiber_count", count(cur, "information_fiber") == 500, count(cur, "information_fiber"), "500")
    add("raw_event_stream_count", count(cur, "raw_event_stream") == 1500, count(cur, "raw_event_stream"), "1500")
    add("p_rows_present", count(cur, "p_predictive_support_v022") > 0, count(cur, "p_predictive_support_v022"), ">0")
    add("r_rows_present", count(cur, "r_counterstructure_v022") > 0, count(cur, "r_counterstructure_v022"), ">0")
    add("xi_rows_present", count(cur, "xi_boundary_guard_v022") > 0, count(cur, "xi_boundary_guard_v022"), ">0")
    # stored gate checks
    add("v08_gates_present", count(cur, "candidate_adoption_gate_v08") >= 6, count(cur, "candidate_adoption_gate_v08"), ">=6")
    add("real_data_gate_blocks_if_fixture", count(cur, "candidate_adoption_gate_v08", "gate_name='external_real_data_trial_gate'") == 1, count(cur, "candidate_adoption_gate_v08", "gate_name='external_real_data_trial_gate'"), "1")

    passed = sum(1 for _, ok, _, _ in checks if ok)
    total = len(checks)
    for name, ok, obs, exp in checks:
        print(f"{'PASS' if ok else 'FAIL'} {name}: observed={obs} expected={exp}")
    print(f"SUMMARY {passed}/{total} PASS")
    con.close()
    return 0 if passed == total else 1

if __name__ == "__main__":
    import os, sys
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
