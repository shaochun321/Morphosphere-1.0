#!/usr/bin/env python3
"""Run v8.5.2 acceptance SQL against a diagnostic DB."""
from __future__ import annotations
import sqlite3, sys, json
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "v85_full_diagnostic_run.db"
checks = [
    ("integrity_check", "PRAGMA integrity_check", lambda r: r[0][0] == "ok"),
    ("execution_mode_diagnostic_full", "SELECT execution_mode FROM run_manifest", lambda r: r and r[0][0] == "diagnostic_full"),
    ("not_scientific_run", "SELECT COUNT(*) FROM run_manifest WHERE execution_mode='scientific_run'", lambda r: r[0][0] == 0),
    ("no_invalid_confirmation_transitions", "SELECT COUNT(*) FROM pr_graph_transition_record WHERE is_valid = 0", lambda r: r[0][0] == 0),
    ("no_masking_supported_synonym", "SELECT COUNT(*) FROM pr_confirmation_graph_record WHERE current_node='masking_supported'", lambda r: r[0][0] == 0),
    ("spike_rate_positive", "SELECT COUNT(*) FROM information_fiber WHERE spike_rate > 0", lambda r: r[0][0] > 0),
    ("spike_rate_nonuniform", "SELECT COUNT(DISTINCT ROUND(spike_rate, 6)) FROM information_fiber", lambda r: r[0][0] > 1),
    ("transport_accepted_rejected", "SELECT COUNT(DISTINCT accepted) FROM transport_current_edge", lambda r: r[0][0] >= 2),
    ("transport_weight_nonuniform", "SELECT COUNT(DISTINCT ROUND(transport_weight, 6)) FROM transport_current_edge", lambda r: r[0][0] > 1),
    ("boundary_or_signal_nonzero", "SELECT COUNT(*) FROM transport_current_edge WHERE boundary_cost != 0 OR signal_drift != 0", lambda r: r[0][0] > 0),
    ("derived_o_candidate", "SELECT COUNT(*) FROM o_candidate_record WHERE formation_mode='derived_minimal'", lambda r: r[0][0] > 0),
    ("o_support_scores", "SELECT COUNT(*) FROM o_candidate_record WHERE support_score IS NOT NULL", lambda r: r[0][0] > 0),
    ("xi_lifecycle_multi_state", "SELECT COUNT(DISTINCT current_state) FROM xi_decay_policy", lambda r: r[0][0] > 1),
    ("xi_non_unknown_types", "SELECT COUNT(*) FROM xi_residue_record WHERE residue_type != 'unknown'", lambda r: r[0][0] > 0),
    ("xi_support_domains", "SELECT COUNT(*) FROM xi_residue_record WHERE spatial_support_cell_uids_json NOT IN ('[]','') AND temporal_support_window_ids_json NOT IN ('[]','') AND source_hypothesis_refs_json NOT IN ('[]','')", lambda r: r[0][0] > 0),
    ("relation_entropy_nonuniform", "SELECT COUNT(DISTINCT ROUND(entropy_value, 6)) FROM relation_entropy_record", lambda r: r[0][0] > 1),
    ("relation_entropy_distribution_recorded", "SELECT COUNT(*) FROM relation_entropy_record WHERE entropy_source_distribution NOT IN ('[]','')", lambda r: r[0][0] > 0),
    ("proxy_provenance_complete_minimum", "SELECT COUNT(*) FROM proxy_provenance", lambda r: r[0][0] >= 7),
    ("manifest_counts_distinguished", "SELECT physical_cell_count,window_count,spacetime_cell_count FROM run_manifest", lambda r: r and r[0][0] > 0 and r[0][1] > 0 and r[0][2] > r[0][0]),
    ("telemetry_present", "SELECT COUNT(*) FROM diagnostic_telemetry_report", lambda r: r[0][0] > 0),
    ("synthetic_emergence_isolated", "SELECT COUNT(*) FROM raw_emergency_export_manifest WHERE production_log_allowed=0 AND scientific_use_allowed=0", lambda r: r[0][0] > 0),
]

def main():
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 2
    conn = sqlite3.connect(DB)
    failed = []
    print(f"DB: {DB}")
    for name, sql, pred in checks:
        try:
            rows = conn.execute(sql).fetchall()
            ok = pred(rows)
        except Exception as e:
            rows = [[f"ERROR: {e}"]]
            ok = False
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {rows}")
        if not ok:
            failed.append(name)
    conn.close()
    print(json.dumps({"passed": len(checks)-len(failed), "failed": failed}, indent=2))
    return 1 if failed else 0
if __name__ == "__main__":
    raise SystemExit(main())
