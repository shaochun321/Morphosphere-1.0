#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone

REQUIRED = [
    "online_sensorium_run_manifest_v03",
    "online_clock_tick_v03",
    "online_preneural_tick_state_v03",
    "online_origin_anchor_tick_v03",
    "online_latent_trajectory_tick_v03",
    "online_o_candidate_tick_v03",
    "online_p_support_tick_v03",
    "online_r_counterstructure_tick_v03",
    "online_xi_boundary_tick_v03",
    "online_feedback_tick_v03",
    "full_replay_scenario_v03",
    "full_replay_event_buffer_v03",
    "full_replay_pr_response_v03",
    "full_replay_result_v03",
    "full_replay_source_integrity_v03",
    "online_sensorium_acceptance_report_v03",
    "online_sensorium_artifact_manifest_v03",
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


def count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())


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
    if not table_exists(conn, "online_sensorium_run_manifest_v03"):
        print("FAIL missing manifest")
        return 1
    m = conn.execute("SELECT * FROM online_sensorium_run_manifest_v03 ORDER BY created_at DESC LIMIT 1").fetchone()
    check("manifest_exists", m is not None, "present" if m else "missing", "present")
    if m:
        check("execution_mode", m["execution_mode"] == "diagnostic_append_only_online_sensorium_full_replay", m["execution_mode"], "diagnostic_append_only_online_sensorium_full_replay")
        check("not_scientific_run", m["scientific_run"] == 0, m["scientific_run"], 0)
        check("semantic_labels_disallowed", m["semantic_labels_allowed"] == 0, m["semantic_labels_allowed"], 0)
        check("system_clock_source", m["clock_source_table"] == "system_clock_entry", m["clock_source_table"], "system_clock_entry")
        clock_count = count(conn, "system_clock_entry")
        check("clock_tick_matches_clock_count", count(conn, "online_clock_tick_v03") == clock_count, count(conn, "online_clock_tick_v03"), clock_count)
        before = json.loads(m["source_fact_counts_before_json"])
        after = json.loads(m["source_fact_counts_after_json"])
        live = {t: count(conn, t) for t in SOURCE_FACTS}
        check("source_fact_counts_unchanged_manifest", before == after, {"before": before, "after": after}, "same")
        check("live_source_counts_match_after", live == after, live, after)
        check("online_preneural_states_positive", m["online_preneural_state_count"] > 0, m["online_preneural_state_count"], ">0")
        check("online_trajectory_ticks_positive", m["online_trajectory_tick_count"] > 0, m["online_trajectory_tick_count"], ">0")
        check("P_support_exists", m["online_p_support_count"] > 0, m["online_p_support_count"], ">0")
        check("R_counter_exists", m["online_r_counter_count"] > 0, m["online_r_counter_count"], ">0")
        check("Xi_guard_exists", m["online_xi_guard_count"] > 0, m["online_xi_guard_count"], ">0")
        check("replay_scenarios_enough", m["replay_scenario_count"] >= 9, m["replay_scenario_count"], ">=9")
        check("replay_events_present", m["replay_event_count"] >= count(conn, "raw_event_stream") * 9, m["replay_event_count"], ">= raw events * 9")
        check("pr_boundary_asserted", "P/R remains before Xi" in m["pr_boundary_assertion"], m["pr_boundary_assertion"], "contains P/R remains before Xi")

    check("no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all direct_to_p_allowed=0", "0 allowed")
    check("no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all direct_to_r_allowed=0", "0 allowed")
    check("R_not_Xi_residue", conn.execute("SELECT COUNT(*) FROM online_r_counterstructure_tick_v03 WHERE forbidden_equivalence LIKE '%not Xi/Xin%'").fetchone()[0] == count(conn, "online_r_counterstructure_tick_v03"), count(conn, "online_r_counterstructure_tick_v03"), "all R rows forbid Xi equivalence")
    check("source_integrity_all_unchanged", conn.execute("SELECT COUNT(*) FROM full_replay_source_integrity_v03 WHERE unchanged != 1").fetchone()[0] == 0, "all unchanged", "0 changed")
    check("replay_buffer_no_source_rewrite", conn.execute("SELECT COUNT(*) FROM full_replay_event_buffer_v03 WHERE source_fact_rewritten != 0").fetchone()[0] == 0, "all replay rows source_fact_rewritten=0", "0")
    # Replay behavior checks.
    res = {r["scenario_name"]: dict(r) for r in conn.execute("SELECT * FROM full_replay_result_v03")}
    check("baseline_passed", res.get("baseline", {}).get("passed") == 1, res.get("baseline"), "passed")
    check("noise_05_passed", res.get("noise_05", {}).get("passed") == 1, res.get("noise_05"), "passed")
    check("noise_10_passed", res.get("noise_10", {}).get("passed") == 1, res.get("noise_10"), "passed")
    check("noise_20_passed", res.get("noise_20", {}).get("passed") == 1, res.get("noise_20"), "passed")
    check("noise_30_passed", res.get("noise_30", {}).get("passed") == 1, res.get("noise_30"), "passed")
    if "noise_05" in res and "noise_30" in res:
        check("xi_increases_with_noise", res["noise_30"]["xi_mass_mean"] > res["noise_05"]["xi_mass_mean"], {"noise_05": res["noise_05"]["xi_mass_mean"], "noise_30": res["noise_30"]["xi_mass_mean"]}, "noise_30 > noise_05")
        check("low_noise_p_stable", res["noise_10"]["p_stability_mean"] > 0.68, res["noise_10"]["p_stability_mean"], ">0.68")
    hidden = res.get("hidden_structure_lowfreq", {})
    check("hidden_structure_passed", hidden.get("passed") == 1, hidden, "passed")
    check("hidden_contrast_positive", hidden.get("hidden_detection_contrast", 0.0) > 0.45, hidden.get("hidden_detection_contrast"), ">0.45")
    perm = res.get("cell_id_permutation", {})
    check("cell_id_permutation_passed", perm.get("passed") == 1, perm, "passed")
    check("cell_id_invariant_high", perm.get("cell_id_invariant_score", 0.0) > 0.90, perm.get("cell_id_invariant_score"), ">0.90")
    phase = res.get("cross_modal_phase_shift", {})
    check("phase_shift_passed", phase.get("passed") == 1, phase, "passed")
    phys = res.get("physics_swap_MET_proxy", {})
    check("physics_swap_passed", phys.get("passed") == 1, phys, "passed")
    check("physics_swap_nonuniform", phys.get("physics_signal_nonuniformity", 0.0) > 0.5, phys.get("physics_signal_nonuniformity"), ">0.5")
    # Online P/R/Xi must be tick-wise, not merely old table replay.
    check("online_p_ticks_cover_o_ticks", count(conn, "online_p_support_tick_v03") == count(conn, "online_o_candidate_tick_v03"), {"P": count(conn, "online_p_support_tick_v03"), "O": count(conn, "online_o_candidate_tick_v03")}, "P = O")
    check("online_clock_ordered", conn.execute("SELECT MIN(tick_n), MAX(tick_n), COUNT(DISTINCT tick_n) FROM online_clock_tick_v03").fetchone()[2] == count(conn, "system_clock_entry"), "distinct ticks match", "clock count")
    check("artifact_manifest_present", count(conn, "online_sensorium_artifact_manifest_v03") >= 4, count(conn, "online_sensorium_artifact_manifest_v03"), ">=4")

    # Store acceptance rows into the DB for release audit. Refresh only v03 acceptance rows.
    conn.execute("DELETE FROM online_sensorium_acceptance_report_v03")
    tnow = now()
    run_id = m["online_run_id"] if m else "missing"
    for t in tests:
        conn.execute(
            "INSERT INTO online_sensorium_acceptance_report_v03 VALUES (?,?,?,?,?,?,?)",
            (
                "accv03_" + t["test_name"][:80], run_id, t["test_name"], "PASS" if t["passed"] else "FAIL",
                json.dumps(t["observed"], ensure_ascii=False, default=str), json.dumps(t["expected"], ensure_ascii=False, default=str), tnow,
            ),
        )
    conn.commit()
    stored = conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) FROM online_sensorium_acceptance_report_v03").fetchone()
    check("stored_acceptance_all_pass", stored[0] == stored[1] and stored[0] > 0, f"{stored[1]}/{stored[0]}", "all pass")

    passed = sum(1 for t in tests if t["passed"])
    total = len(tests)
    for t in tests:
        print(f"{'PASS' if t['passed'] else 'FAIL'} {t['test_name']}: observed={t['observed']} expected={t['expected']}")
    print(f"online_sensorium_v0.3 acceptance: {passed}/{total} PASS")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "total": total, "results": tests}, f, ensure_ascii=False, indent=2)
    conn.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
