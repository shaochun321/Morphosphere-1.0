#!/usr/bin/env python3
"""Acceptance checks for Morphosphere dynamic_recursive_v0.2."""
from __future__ import annotations
import argparse
import json
import sqlite3
import sys

REQUIRED_TABLES = [
    "recursive_system_run_manifest",
    "clock_binding_record",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "preneural_node_state",
    "preneural_edge_state",
    "dynamic_origin_anchor_state",
    "dynamic_latent_trajectory_state",
    "trajectory_transition_edge",
    "topdown_feedback_signal",
    "xin_residue_dynamics",
    "recursive_memory_trace",
    "recursive_metric_weight_state",
    "dynamic_free_energy_trace",
    "recursive_iteration_report",
    "recursive_reprojection_report",
    "recursive_acceptance_report",
]


def scalar(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db")
    parser.add_argument("--json", default="")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    results = []
    def check(name, condition, observed, expected):
        results.append({
            "test_name": name,
            "passed": bool(condition),
            "observed": observed,
            "expected": expected,
        })

    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in REQUIRED_TABLES:
        check(f"table_exists_{table}", table in tables, table in tables, "table exists")

    manifest = conn.execute("SELECT * FROM recursive_system_run_manifest ORDER BY created_at DESC LIMIT 1").fetchone()
    check("manifest_exists", manifest is not None, "present" if manifest else "missing", "present")
    run_id = manifest["recursive_run_id"] if manifest else ""

    if manifest:
        check("version_dynamic_recursive_v02", manifest["recursive_version"] == "dynamic_recursive_v0.2", manifest["recursive_version"], "dynamic_recursive_v0.2")
        check("execution_mode_diagnostic_recursive", manifest["execution_mode"] == "diagnostic_recursive", manifest["execution_mode"], "diagnostic_recursive")
        check("not_scientific_run", manifest["scientific_run"] == 0, manifest["scientific_run"], "0")
        check("semantic_labels_disallowed", manifest["semantic_labels_allowed"] == 0, manifest["semantic_labels_allowed"], "0")
        check("clock_source_system_clock_entry", manifest["clock_source_table"] == "system_clock_entry", manifest["clock_source_table"], "system_clock_entry")
        check("iterations_at_least_5", manifest["iteration_count"] >= 5, manifest["iteration_count"], ">=5")
        check("input_tables_do_not_include_semantic", "semantic_readout" not in manifest["input_tables_json"] and "object_hypothesis" not in manifest["input_tables_json"], manifest["input_tables_json"], "no semantic/O/P generation tables")

    if run_id:
        acc_total = scalar(conn, "SELECT COUNT(*) FROM recursive_acceptance_report WHERE recursive_run_id=?", (run_id,))
        acc_pass = scalar(conn, "SELECT COUNT(*) FROM recursive_acceptance_report WHERE recursive_run_id=? AND passed=1", (run_id,))
        check("stored_acceptance_all_pass", acc_total > 0 and acc_total == acc_pass, f"{acc_pass}/{acc_total}", "all stored recursive checks pass")
        clock_count = scalar(conn, "SELECT COUNT(*) FROM clock_binding_record WHERE recursive_run_id=? AND clock_source_table='system_clock_entry'", (run_id,))
        check("clock_binding_recorded", clock_count == 1, clock_count, "1")
        cell_coords = scalar(conn, "SELECT COUNT(*) FROM cell_spatial_coordinate_snapshot WHERE recursive_run_id=?", (run_id,))
        info_coords = scalar(conn, "SELECT COUNT(*) FROM information_relative_coordinate_snapshot WHERE recursive_run_id=?", (run_id,))
        raw_events = scalar(conn, "SELECT COUNT(*) FROM raw_event_stream")
        spacetime_cells = scalar(conn, "SELECT COUNT(*) FROM spacetime_cell")
        check("cell_coordinate_snapshot_count_matches", cell_coords == spacetime_cells, f"{cell_coords}/{spacetime_cells}", "match")
        check("information_coordinate_snapshot_count_matches", info_coords == raw_events, f"{info_coords}/{raw_events}", "match")
        pr_nodes = scalar(conn, "SELECT COUNT(*) FROM preneural_node_state WHERE recursive_run_id=?", (run_id,))
        pr_edges = scalar(conn, "SELECT COUNT(*) FROM preneural_edge_state WHERE recursive_run_id=?", (run_id,))
        dyn_states = scalar(conn, "SELECT COUNT(*) FROM dynamic_latent_trajectory_state WHERE recursive_run_id=?", (run_id,))
        feedback = scalar(conn, "SELECT COUNT(*) FROM topdown_feedback_signal WHERE recursive_run_id=?", (run_id,))
        xin_states = scalar(conn, "SELECT COUNT(DISTINCT dynamic_state) FROM xin_residue_dynamics WHERE recursive_run_id=?", (run_id,))
        check("preneural_node_states_present", pr_nodes > 0, pr_nodes, ">0")
        check("preneural_edge_states_present", pr_edges > 0, pr_edges, ">0")
        check("dynamic_trajectory_states_present", dyn_states > 0, dyn_states, ">0")
        check("topdown_feedback_present", feedback > 0, feedback, ">0")
        check("xin_multistate", xin_states >= 3, xin_states, ">=3")
        first = conn.execute("SELECT * FROM recursive_iteration_report WHERE recursive_run_id=? ORDER BY iteration_n ASC LIMIT 1", (run_id,)).fetchone()
        last = conn.execute("SELECT * FROM recursive_iteration_report WHERE recursive_run_id=? ORDER BY iteration_n DESC LIMIT 1", (run_id,)).fetchone()
        if first and last:
            check("prediction_error_not_worse", last["avg_prediction_error"] <= first["avg_prediction_error"] * 1.05 + 1e-9, f"{first['avg_prediction_error']:.6f}->{last['avg_prediction_error']:.6f}", "<=105%")
            check("xin_mass_not_worse", last["avg_xin_residual_mass"] <= first["avg_xin_residual_mass"] * 1.05 + 1e-9, f"{first['avg_xin_residual_mass']:.6f}->{last['avg_xin_residual_mass']:.6f}", "<=105%")
            check("free_energy_not_worse", last["free_energy_proxy"] <= first["free_energy_proxy"] * 1.05 + 1e-9, f"{first['free_energy_proxy']:.6f}->{last['free_energy_proxy']:.6f}", "<=105%")
        rrp = conn.execute("SELECT * FROM recursive_reprojection_report WHERE recursive_run_id=? ORDER BY iteration_n DESC LIMIT 1", (run_id,)).fetchone()
        if rrp:
            check("reprojection_beats_baseline", rrp["improvement_over_baseline"] > 0.30, f"{rrp['improvement_over_baseline']:.6f}", ">0.30")
        weight_rows = scalar(conn, "SELECT COUNT(*) FROM recursive_metric_weight_state WHERE recursive_run_id=?", (run_id,))
        check("metric_weight_rows_present", weight_rows >= 5, weight_rows, ">=5")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    for r in results:
        print(f"{'PASS' if r['passed'] else 'FAIL'} {r['test_name']}: observed={r['observed']} expected={r['expected']}")
    print(f"dynamic_recursive_v0.2 acceptance: {passed}/{total} PASS")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "total": total, "results": results}, f, ensure_ascii=False, indent=2)
    conn.close()
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
