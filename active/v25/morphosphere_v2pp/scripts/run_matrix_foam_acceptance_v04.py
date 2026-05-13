#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone

REQUIRED = [
    "matrix_foam_run_manifest_v04",
    "substrate_material_region_v04",
    "cell_matrix_contact_v04",
    "foam_edge_state_v04",
    "substrate_stress_tensor_v04",
    "physical_data_source_manifest_v04",
    "physical_sample_stream_v04",
    "physical_driver_mapping_v04",
    "mechanotransduction_event_v04",
    "substrate_to_raw_event_projection_v04",
    "matrix_foam_replay_result_v04",
    "matrix_foam_acceptance_report_v04",
    "matrix_foam_artifact_manifest_v04",
]
SOURCE_FACTS = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "system_clock_entry",
]


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


def count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--json", default="")
    args = ap.parse_args()
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    tests = []

    def check(name: str, cond: bool, observed, expected):
        tests.append({"test_name": name, "passed": bool(cond), "observed": observed, "expected": expected})

    for table in REQUIRED:
        check(f"table_exists_{table}", table_exists(conn, table), table_exists(conn, table), "exists")
    if not table_exists(conn, "matrix_foam_run_manifest_v04"):
        print("FAIL missing matrix_foam_run_manifest_v04")
        return 1
    m = conn.execute("SELECT * FROM matrix_foam_run_manifest_v04 ORDER BY created_at DESC LIMIT 1").fetchone()
    check("manifest_exists", m is not None, "present" if m else "missing", "present")
    if m:
        check("execution_mode", m["execution_mode"] == "diagnostic_append_only_matrix_foam_physical_driver", m["execution_mode"], "diagnostic_append_only_matrix_foam_physical_driver")
        check("not_scientific_run", m["scientific_run"] == 0, m["scientific_run"], 0)
        check("clock_source", m["clock_source_table"] == "system_clock_entry", m["clock_source_table"], "system_clock_entry")
        before = json.loads(m["source_fact_counts_before_json"])
        after = json.loads(m["source_fact_counts_after_json"])
        live = {t: count(conn, t) for t in SOURCE_FACTS}
        check("source_fact_counts_unchanged", before == after, {"before": before, "after": after}, "same")
        check("live_source_counts_match_manifest", live == after, live, after)
        check("material_regions_four", m["material_region_count"] >= 4, m["material_region_count"], ">=4")
        check("contacts_match_spacetime_cells", m["cell_matrix_contact_count"] == count(conn, "spacetime_cell"), m["cell_matrix_contact_count"], count(conn, "spacetime_cell"))
        check("foam_edges_dense", m["foam_edge_count"] >= count(conn, "spacetime_cell") * 2, m["foam_edge_count"], ">= 2 * spacetime_cell")
        check("stress_tensor_per_cell", m["stress_tensor_count"] == count(conn, "spacetime_cell"), m["stress_tensor_count"], count(conn, "spacetime_cell"))
        check("physical_samples_present", m["physical_sample_count"] >= count(conn, "system_clock_entry") * 4, m["physical_sample_count"], ">= clock_count * 4")
        check("met_events_present", m["mechanotransduction_event_count"] >= m["physical_sample_count"], m["mechanotransduction_event_count"], ">= physical samples")
        check("projections_present", m["projection_count"] == m["mechanotransduction_event_count"], m["projection_count"], "= MET events")
        check("pr_xi_boundary_asserted", "P/R remains" in m["pr_xi_boundary_assertion"], m["pr_xi_boundary_assertion"], "contains P/R remains")

    # Physical driver manifest boundary.
    ds = conn.execute("SELECT * FROM physical_data_source_manifest_v04 LIMIT 1").fetchone()
    check("physical_source_manifest_exists", ds is not None, "present" if ds else "missing", "present")
    if ds:
        check("fixture_or_external_driver_mode", ds["driver_mode"] in {"deterministic_fixture_csv_plus_external_csv_ready", "external_csv_read_only"}, ds["driver_mode"], "known driver mode")
        check("no_experimental_truth_claim", ds["real_experimental_data_claimed"] == 0, ds["real_experimental_data_claimed"], 0)
        check("driver_read_only_boundary", "read-only" in ds["allowed_use"], ds["allowed_use"], "contains read-only")
        check("physical_sample_count_matches_manifest", ds["sample_count"] == count(conn, "physical_sample_stream_v04"), ds["sample_count"], count(conn, "physical_sample_stream_v04"))

    # Material and foam diversity.
    mats = [r[0] for r in conn.execute("SELECT DISTINCT region_name FROM substrate_material_region_v04")]
    check("material_region_names_include_foam", "foam_crosslink" in mats, mats, "include foam_crosslink")
    check("material_region_names_include_shear", "shear_band" in mats, mats, "include shear_band")
    edge_types = [r[0] for r in conn.execute("SELECT DISTINCT edge_type FROM foam_edge_state_v04")]
    check("foam_edge_types_three", len(edge_types) >= 3, edge_types, ">=3 edge types")
    check("phase_supporting_edges_present", conn.execute("SELECT COUNT(*) FROM foam_edge_state_v04 WHERE supports_signal_phase=1").fetchone()[0] > 0, "phase-supporting edges", ">0")

    # MET and projection behavior.
    gate_stats = conn.execute("SELECT MIN(met_gate_probability), MAX(met_gate_probability), AVG(met_gate_probability) FROM mechanotransduction_event_v04").fetchone()
    check("met_gate_in_unit_range", 0.0 <= gate_stats[0] <= gate_stats[1] <= 1.0, tuple(gate_stats), "0 <= min <= max <= 1")
    check("met_gate_nonuniform", (gate_stats[1] - gate_stats[0]) > 0.05, tuple(gate_stats), "range > 0.05")
    conf = conn.execute("SELECT AVG(projection_confidence), MAX(source_fact_rewritten) FROM substrate_to_raw_event_projection_v04").fetchone()
    check("projection_confidence_positive", conf[0] > 0.45, conf[0], ">0.45")
    check("projection_no_source_rewrite", conf[1] == 0, conf[1], 0)

    # Replay behavior checks.
    res = {r["scenario_name"]: dict(r) for r in conn.execute("SELECT * FROM matrix_foam_replay_result_v04")}
    check("replay_scenarios_count", len(res) >= 9, len(res), ">=9")
    check("all_replay_scenarios_pass", all(r["passed"] == 1 for r in res.values()), {k: v["passed"] for k, v in res.items()}, "all passed")
    if "force_noise_10" in res and "force_noise_30" in res:
        check("xi_pressure_increases_with_force_noise", res["force_noise_30"]["xi_pressure_proxy"] > res["force_noise_10"]["xi_pressure_proxy"], {"force_noise_10": res["force_noise_10"]["xi_pressure_proxy"], "force_noise_30": res["force_noise_30"]["xi_pressure_proxy"]}, "30% > 10%")
        check("p_stability_decreases_with_force_noise", res["force_noise_30"]["p_stability_proxy"] < res["force_noise_10"]["p_stability_proxy"], {"force_noise_10": res["force_noise_10"]["p_stability_proxy"], "force_noise_30": res["force_noise_30"]["p_stability_proxy"]}, "30% < 10%")
    if "matrix_edge_ablation" in res and "baseline_substrate" in res:
        check("edge_ablation_degrades_integrity", res["matrix_edge_ablation"]["substrate_integrity_proxy"] < res["baseline_substrate"]["substrate_integrity_proxy"], {"baseline": res["baseline_substrate"]["substrate_integrity_proxy"], "ablation": res["matrix_edge_ablation"]["substrate_integrity_proxy"]}, "ablation < baseline")
    if "shear_wave_injection" in res:
        check("shear_wave_raises_counterstructure", res["shear_wave_injection"]["r_counter_proxy"] > 0.18, res["shear_wave_injection"]["r_counter_proxy"], ">0.18")

    # P/R/Xi boundary inherited from v0.3 and v0.2.2 must remain intact.
    if table_exists(conn, "online_xi_boundary_tick_v03"):
        check("v03_no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all zero", "0")
        check("v03_no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all zero", "0")
    if table_exists(conn, "xi_boundary_guard_v022"):
        check("v022_no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all zero", "0")
        check("v022_no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all zero", "0")

    check("artifact_manifest_present", count(conn, "matrix_foam_artifact_manifest_v04") >= 3, count(conn, "matrix_foam_artifact_manifest_v04"), ">=3")

    # Store acceptance rows.
    run_id = m["matrix_run_id"] if m else "missing"
    conn.execute("DELETE FROM matrix_foam_acceptance_report_v04")
    tnow = now()
    for t in tests:
        conn.execute(
            "INSERT INTO matrix_foam_acceptance_report_v04 VALUES (?,?,?,?,?,?,?)",
            ("accv04_" + t["test_name"][:80], run_id, t["test_name"], "PASS" if t["passed"] else "FAIL", json.dumps(t["observed"], ensure_ascii=False, default=str), json.dumps(t["expected"], ensure_ascii=False, default=str), tnow),
        )
    conn.commit()
    stored = conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) FROM matrix_foam_acceptance_report_v04").fetchone()
    check("stored_acceptance_all_pass", stored[0] == stored[1] and stored[0] > 0, f"{stored[1]}/{stored[0]}", "all pass")

    passed = sum(1 for t in tests if t["passed"])
    total = len(tests)
    for t in tests:
        print(f"{'PASS' if t['passed'] else 'FAIL'} {t['test_name']}: observed={t['observed']} expected={t['expected']}")
    print(f"matrix_foam_physical_driver_v0.4 acceptance: {passed}/{total} PASS")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "total": total, "results": tests}, f, ensure_ascii=False, indent=2)
    conn.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
