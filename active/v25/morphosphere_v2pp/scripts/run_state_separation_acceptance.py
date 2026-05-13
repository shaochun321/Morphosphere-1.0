#!/usr/bin/env python3
"""Acceptance checks for state_separation_v0.1 diagnostic output."""
from __future__ import annotations
import json
import sqlite3
import sys
from pathlib import Path

DB = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "outputs" / "morphosphere_state_separation_v01_output_database.db"

CHECKS = [
    ("integrity_check", "PRAGMA integrity_check", lambda r: r and r[0][0] == "ok"),
    ("state_manifest_present", "SELECT COUNT(*) FROM state_core_run_manifest WHERE state_version='state_separation_v0.1' AND execution_mode='diagnostic_state_separation'", lambda r: r[0][0] >= 1),
    ("not_scientific_run", "SELECT COUNT(*) FROM state_core_run_manifest WHERE scientific_run != 0 OR semantic_labels_allowed != 0", lambda r: r[0][0] == 0),
    ("physical_first_assertion_recorded", "SELECT COUNT(*) FROM state_core_run_manifest WHERE physical_first_assertion LIKE '%spacetime%before%inverse%'", lambda r: r[0][0] >= 1),
    ("raw_events_present", "SELECT COUNT(*) FROM raw_event_stream", lambda r: r[0][0] >= 1000),
    ("raw_events_multi_channel", "SELECT COUNT(DISTINCT channel_type) FROM raw_event_stream", lambda r: r[0][0] >= 3),
    ("origin_anchors_present", "SELECT COUNT(*) FROM origin_anchor", lambda r: r[0][0] >= 10),
    ("latent_trajectories_nonsemantic", "SELECT COUNT(*) FROM latent_trajectory WHERE formation_mode='nonsemantic_spacetime_decomposition' AND semantic_label IS NULL", lambda r: r[0][0] >= 2),
    ("trajectory_scores_nonzero", "SELECT AVG(continuity_score), AVG(conservation_score), AVG(phase_coherence_score), AVG(reconstruction_score) FROM latent_trajectory", lambda r: r and all(x is not None and x > 0 for x in r[0])),
    ("trajectory_bindings_present", "SELECT COUNT(*), SUM(accepted) FROM trajectory_event_binding", lambda r: r and r[0][0] >= 1000 and r[0][1] > 0),
    ("xin_residue_retained", "SELECT COUNT(*) FROM xin_residue_state WHERE residue_mass > 0", lambda r: r[0][0] > 0),
    ("reprojection_passed", "SELECT COUNT(*) FROM trajectory_reprojection_report WHERE passed=1 AND improvement_over_global > 0.10", lambda r: r[0][0] >= 1),
    ("noise_sweep_complete", "SELECT COUNT(DISTINCT noise_level) FROM state_separation_noise_sweep", lambda r: r[0][0] >= 4),
    ("noise_sweep_not_collapsed_10pct", "SELECT MIN(coassignment_stability) FROM state_separation_noise_sweep WHERE noise_level <= 0.10", lambda r: r and r[0][0] is not None and r[0][0] >= 0.70),
    ("noise_xin_increases", "SELECT (SELECT xin_residue_mass_proxy FROM state_separation_noise_sweep ORDER BY noise_level ASC LIMIT 1), (SELECT xin_residue_mass_proxy FROM state_separation_noise_sweep ORDER BY noise_level DESC LIMIT 1)", lambda r: r and r[0][1] > r[0][0]),
    ("hidden_structure_probe_passed", "SELECT COUNT(*) FROM injected_structure_probe WHERE passed=1 AND detected_as='xi_proto_candidate'", lambda r: r[0][0] >= 1),
    ("cross_modal_binding_passed", "SELECT AVG(accepted) FROM cross_modal_binding_probe", lambda r: r and r[0][0] is not None and r[0][0] >= 0.50),
    ("all_state_tests_passed", "SELECT COUNT(*) FROM state_separation_test_report WHERE passed=0", lambda r: r[0][0] == 0),
]


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 2
    conn = sqlite3.connect(str(DB))
    failed = []
    print(f"DB: {DB}")
    for name, sql, pred in CHECKS:
        try:
            rows = conn.execute(sql).fetchall()
            ok = bool(pred(rows))
        except Exception as exc:
            rows = [[f"ERROR: {exc}"]]
            ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {rows}")
        if not ok:
            failed.append(name)
    conn.close()
    print(json.dumps({"passed": len(CHECKS) - len(failed), "failed": failed}, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
