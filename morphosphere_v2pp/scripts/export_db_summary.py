#!/usr/bin/env python3
"""Export a compact, reproducible summary of a Morphosphere v8.5.2 diagnostic DB.

This script is intentionally stdlib-only so users can run it immediately after
unzip without installing the project package.
"""
from __future__ import annotations
import json
import sqlite3
import sys
from pathlib import Path

DEFAULT_TABLES = [
    "run_manifest",
    "system_clock_entry",
    "spacetime_cell",
    "information_fiber",
    "transport_current_edge",
    "o_candidate_record",
    "object_hypothesis",
    "xi_residue_record",
    "xi_decay_policy",
    "relation_entropy_record",
    "proxy_provenance",
    "diagnostic_telemetry_report",
    "v85_to_mainline_crosswalk",
    "raw_emergency_export_manifest",
    "perturbation_run_manifest",
    "perturbation_effect_report",
    "threshold_sweep_record",
    "failed_expectation_report",
    "transport_cost_matrix_record",
    "xi_residue_mass_record",
    "v853_reproducibility_report",
    "v853_release_artifact_manifest",
]


def scalar(conn: sqlite3.Connection, sql: str, default=None):
    try:
        row = conn.execute(sql).fetchone()
        if row is None:
            return default
        return row[0]
    except sqlite3.Error:
        return default


def rows(conn: sqlite3.Connection, sql: str):
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    except sqlite3.Error as e:
        return [{"error": str(e), "sql": sql}]


def table_count(conn: sqlite3.Connection, table: str):
    return scalar(conn, f"SELECT COUNT(*) FROM {table}", 0)


def main() -> int:
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("v85_full_diagnostic_run.db")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("reports/db_summary.json")
    if not db.exists():
        print(f"DB not found: {db}")
        return 2
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    summary = {
        "db_path": str(db),
        "integrity_check": scalar(conn, "PRAGMA integrity_check"),
        "tables": {t: table_count(conn, t) for t in DEFAULT_TABLES},
        "manifest": rows(conn, "SELECT run_id,execution_mode,cell_count,physical_cell_count,window_count,spacetime_cell_count,calibration_profile,schema_version FROM run_manifest"),
        "fiber_spike_rate": rows(conn, "SELECT COUNT(*) AS total, SUM(CASE WHEN spike_rate>0 THEN 1 ELSE 0 END) AS positive, COUNT(DISTINCT ROUND(spike_rate,6)) AS distinct_values, MIN(spike_rate) AS min_spike_rate, MAX(spike_rate) AS max_spike_rate, AVG(spike_rate) AS avg_spike_rate FROM information_fiber"),
        "transport": rows(conn, "SELECT COUNT(*) AS total, COUNT(DISTINCT accepted) AS accepted_states, COUNT(DISTINCT ROUND(transport_weight,6)) AS distinct_weights, SUM(CASE WHEN accepted=1 THEN 1 ELSE 0 END) AS accepted_rows, SUM(CASE WHEN accepted=0 THEN 1 ELSE 0 END) AS rejected_rows, MIN(total_cost) AS min_total_cost, MAX(total_cost) AS max_total_cost FROM transport_current_edge"),
        "o_candidate_modes": rows(conn, "SELECT formation_mode, COUNT(*) AS count FROM o_candidate_record GROUP BY formation_mode"),
        "xi_states": rows(conn, "SELECT current_state, COUNT(*) AS count FROM xi_decay_policy GROUP BY current_state"),
        "relation_entropy": rows(conn, "SELECT COUNT(*) AS total, COUNT(DISTINCT ROUND(entropy_value,6)) AS distinct_entropy, MIN(entropy_value) AS min_entropy, MAX(entropy_value) AS max_entropy FROM relation_entropy_record"),
        "proxy_provenance_targets": rows(conn, "SELECT target_field, proxy_type, replacement_condition FROM proxy_provenance ORDER BY target_field"),
        "crosswalk": rows(conn, "SELECT diagnostic_table, mainline_concept, mapping_status, allowed_use, forbidden_use FROM v85_to_mainline_crosswalk ORDER BY diagnostic_table"),
        "v853_effects": rows(conn, "SELECT perturbation_type, target_metric, baseline_value, perturbed_value, delta_value, passed FROM perturbation_effect_report ORDER BY created_at, perturbation_type"),
        "threshold_sweep": rows(conn, "SELECT sweep_dimension, metric_name, COUNT(*) AS rows, MIN(metric_value) AS min_metric, MAX(metric_value) AS max_metric FROM threshold_sweep_record GROUP BY sweep_dimension, metric_name ORDER BY sweep_dimension, metric_name"),
        "failed_expectations": rows(conn, "SELECT check_name, expected_behavior, observed_behavior, severity FROM failed_expectation_report ORDER BY created_at"),
        "release_artifacts": rows(conn, "SELECT artifact_role, artifact_path, size_bytes, sha256 FROM v853_release_artifact_manifest ORDER BY artifact_role"),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out}")
    print(json.dumps({"integrity_check": summary["integrity_check"], "tables": summary["tables"]}, indent=2))
    return 0 if summary["integrity_check"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
