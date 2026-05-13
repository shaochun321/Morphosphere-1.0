#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone

REQUIRED = [
    "neuromorphic_run_manifest_v05",
    "preneural_device_model_registry_v05",
    "preneural_synaptic_edge_v05",
    "device_edge_tick_state_v05",
    "memristive_plasticity_update_v05",
    "neuromorphic_event_projection_v05",
    "preneural_membrane_state_v05",
    "device_pr_evidence_v05",
    "device_neutral_replay_result_v05",
    "neuromorphic_boundary_contract_v05",
    "neuromorphic_acceptance_report_v05",
    "neuromorphic_artifact_manifest_v05",
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
    if not table_exists(conn, "neuromorphic_run_manifest_v05"):
        print("FAIL missing neuromorphic_run_manifest_v05")
        return 1
    m = conn.execute("SELECT * FROM neuromorphic_run_manifest_v05 ORDER BY created_at DESC LIMIT 1").fetchone()
    check("manifest_exists", m is not None, "present" if m else "missing", "present")
    if m:
        check("execution_mode", m["execution_mode"] == "diagnostic_append_only_device_neutral_preneural_edge", m["execution_mode"], "diagnostic_append_only_device_neutral_preneural_edge")
        check("not_scientific_run", m["scientific_run"] == 0, m["scientific_run"], 0)
        check("no_hardware_claim", m["hardware_claimed"] == 0, m["hardware_claimed"], 0)
        check("clock_source", m["clock_source_table"] == "system_clock_entry", m["clock_source_table"], "system_clock_entry")
        before = json.loads(m["source_fact_counts_before_json"])
        after = json.loads(m["source_fact_counts_after_json"])
        live = {t: count(conn, t) for t in SOURCE_FACTS}
        check("source_fact_counts_unchanged", before == after, {"before": before, "after": after}, "same")
        check("live_source_counts_match_manifest", live == after, live, after)
        check("device_model_count_four", m["device_model_count"] == 4, m["device_model_count"], 4)
        check("synaptic_edges_match_foam_edges", m["synaptic_edge_count"] == count(conn, "foam_edge_state_v04"), m["synaptic_edge_count"], count(conn, "foam_edge_state_v04"))
        check("edge_tick_matches_synaptic", m["edge_tick_state_count"] == m["synaptic_edge_count"], m["edge_tick_state_count"], "= synaptic_edge_count")
        check("plasticity_matches_edges", m["plasticity_update_count"] == m["edge_tick_state_count"], m["plasticity_update_count"], "= edge_tick_state_count")
        check("event_projection_matches_met_events", m["event_projection_count"] == count(conn, "mechanotransduction_event_v04"), m["event_projection_count"], count(conn, "mechanotransduction_event_v04"))
        check("membrane_states_match_preneural_nodes", m["membrane_state_count"] == count(conn, "online_preneural_tick_state_v03"), m["membrane_state_count"], count(conn, "online_preneural_tick_state_v03"))
        check("pr_evidence_matches_online_p", m["pr_evidence_count"] == count(conn, "online_p_support_tick_v03"), m["pr_evidence_count"], count(conn, "online_p_support_tick_v03"))
        check("replay_results_present", m["replay_result_count"] >= 10, m["replay_result_count"], ">=10")
        check("pr_xi_boundary_asserted", "P/R remains" in m["pr_xi_boundary_assertion"], m["pr_xi_boundary_assertion"], "contains P/R remains")

    # Device model registry checks.
    models = [r["model_name"] for r in conn.execute("SELECT * FROM preneural_device_model_registry_v05")]
    check("device_models_named", set(models) == {"ideal_memristive_edge", "noisy_rram_like_edge", "volatile_memristive_edge", "oect_ionic_edge"}, models, "four required models")
    check("all_models_simulated_only", conn.execute("SELECT COUNT(*) FROM preneural_device_model_registry_v05 WHERE simulated_only != 1").fetchone()[0] == 0, "all simulated", "simulated_only=1")
    check("all_models_have_noise_or_memory", conn.execute("SELECT COUNT(*) FROM preneural_device_model_registry_v05 WHERE retention_decay < 0 OR hysteresis < 0 OR update_gain <= 0").fetchone()[0] == 0, "valid", "valid params")
    check("hardware_forbidden_claims_present", conn.execute("SELECT COUNT(*) FROM preneural_device_model_registry_v05 WHERE forbidden_claim LIKE '%hardware%' OR forbidden_claim LIKE '%real%' ").fetchone()[0] >= 4, "forbidden claims", ">=4")

    # Edge diversity and dynamics.
    edge_models = [r[0] for r in conn.execute("SELECT DISTINCT device_model_name FROM preneural_synaptic_edge_v05")]
    edge_types = [r[0] for r in conn.execute("SELECT DISTINCT edge_type FROM preneural_synaptic_edge_v05")]
    check("synaptic_edges_use_all_device_models", len(edge_models) == 4, edge_models, "4 models")
    check("synaptic_edges_use_multiple_foam_edge_types", len(edge_types) >= 3, edge_types, ">=3 foam edge types")
    gstats = conn.execute("SELECT MIN(conductance_after), MAX(conductance_after), AVG(conductance_after) FROM device_edge_tick_state_v05").fetchone()
    check("conductance_in_positive_range", gstats[0] >= 0.0 and gstats[1] <= 1.31, tuple(gstats), "0..1.31")
    check("conductance_nonuniform", (gstats[1] - gstats[0]) > 0.15, tuple(gstats), "range > 0.15")
    memstats = conn.execute("SELECT MIN(memory_state), MAX(memory_state), AVG(memory_state) FROM device_edge_tick_state_v05").fetchone()
    check("memory_state_in_unit_range", 0.0 <= memstats[0] <= memstats[1] <= 1.0, tuple(memstats), "0 <= min <= max <= 1")
    check("memory_state_nonuniform", (memstats[1] - memstats[0]) > 0.10, tuple(memstats), "range > 0.10")
    currents = conn.execute("SELECT MIN(edge_current_proxy), MAX(edge_current_proxy), AVG(ABS(edge_current_proxy)) FROM device_edge_tick_state_v05").fetchone()
    check("edge_current_has_signed_or_nonzero_response", currents[2] > 0.02, tuple(currents), "avg abs >0.02")

    # Plasticity and projections.
    dg = conn.execute("SELECT MIN(delta_g), MAX(delta_g), AVG(delta_g) FROM memristive_plasticity_update_v05").fetchone()
    check("plasticity_has_potentiation_and_depression", dg[0] < 0 and dg[1] > 0, tuple(dg), "min<0 and max>0")
    check("bounded_updates_applied", conn.execute("SELECT COUNT(*) FROM memristive_plasticity_update_v05 WHERE bounded_update_applied != 1").fetchone()[0] == 0, "all bounded", "bounded_update_applied=1")
    proj = conn.execute("SELECT AVG(projection_confidence), MAX(source_fact_rewritten), AVG(ABS(device_weighted_signal)) FROM neuromorphic_event_projection_v05").fetchone()
    check("projection_confidence_positive", proj[0] > 0.55, proj[0], ">0.55")
    check("projection_no_source_rewrite", proj[1] == 0, proj[1], 0)
    check("projection_signal_nonzero", proj[2] > 0.02, proj[2], ">0.02")

    # Membrane state.
    act = conn.execute("SELECT MIN(activation_proxy), MAX(activation_proxy), AVG(activation_proxy) FROM preneural_membrane_state_v05").fetchone()
    check("membrane_activation_in_unit_range", 0.0 <= act[0] <= act[1] <= 1.0, tuple(act), "0..1")
    check("membrane_activation_nonuniform", (act[1] - act[0]) > 0.03, tuple(act), "range >0.03")
    unc = conn.execute("SELECT MIN(uncertainty_proxy), MAX(uncertainty_proxy) FROM preneural_membrane_state_v05").fetchone()
    check("membrane_uncertainty_in_unit_range", 0.0 <= unc[0] <= unc[1] <= 1.0, tuple(unc), "0..1")

    # P/R/Xi boundary and evidence channel.
    check("device_no_direct_p_creation", conn.execute("SELECT COUNT(*) FROM device_pr_evidence_v05 WHERE direct_p_creation_allowed != 0").fetchone()[0] == 0, "all zero", "0")
    check("device_no_direct_r_creation", conn.execute("SELECT COUNT(*) FROM device_pr_evidence_v05 WHERE direct_r_creation_allowed != 0").fetchone()[0] == 0, "all zero", "0")
    check("device_no_direct_xi_creation", conn.execute("SELECT COUNT(*) FROM device_pr_evidence_v05 WHERE direct_xi_creation_allowed != 0").fetchone()[0] == 0, "all zero", "0")
    effects = [r[0] for r in conn.execute("SELECT DISTINCT suggested_effect FROM device_pr_evidence_v05")]
    check("device_evidence_has_effect_diversity", len(effects) >= 2, effects, ">=2 effects")
    adj = conn.execute("SELECT MIN(diagnostic_pr_adjustment_proxy), MAX(diagnostic_pr_adjustment_proxy) FROM device_pr_evidence_v05").fetchone()
    check("device_adjustments_bounded", adj[0] >= -0.151 and adj[1] <= 0.151, tuple(adj), "within +/-0.15")

    # Replay behavior.
    res = {r["scenario_name"]: dict(r) for r in conn.execute("SELECT * FROM device_neutral_replay_result_v05")}
    check("replay_scenarios_count", len(res) >= 10, len(res), ">=10")
    check("all_replay_scenarios_pass", all(r["passed"] == 1 for r in res.values()), {k: v["passed"] for k, v in res.items()}, "all passed")
    check("replay_no_source_rewrite", all(r["source_fact_rewrite_count"] == 0 for r in res.values()), "all zero", "0")
    if "read_noise_10" in res and "read_noise_30" in res:
        check("noise_raises_xi_pressure", res["read_noise_30"]["xi_pressure_proxy"] > res["read_noise_10"]["xi_pressure_proxy"], {"10": res["read_noise_10"]["xi_pressure_proxy"], "30": res["read_noise_30"]["xi_pressure_proxy"]}, "30 > 10")
        check("noise_lowers_p_stability", res["read_noise_30"]["p_stability_proxy"] < res["read_noise_10"]["p_stability_proxy"], {"10": res["read_noise_10"]["p_stability_proxy"], "30": res["read_noise_30"]["p_stability_proxy"]}, "30 < 10")
    if "retention_loss" in res and "baseline_device" in res:
        check("retention_loss_reduces_memory", res["retention_loss"]["memory_retention_proxy"] < res["baseline_device"]["memory_retention_proxy"], {"baseline": res["baseline_device"]["memory_retention_proxy"], "retention_loss": res["retention_loss"]["memory_retention_proxy"]}, "retention loss < baseline")
    if "edge_stuck_on" in res:
        check("stuck_on_fault_raises_counter", res["edge_stuck_on"]["r_counter_proxy"] > 0.30, res["edge_stuck_on"]["r_counter_proxy"], ">0.30")
    if "edge_stuck_off" in res:
        check("stuck_off_fault_raises_xi", res["edge_stuck_off"]["xi_pressure_proxy"] > 0.40, res["edge_stuck_off"]["xi_pressure_proxy"], ">0.40")

    # Boundary contracts.
    contracts = [r["boundary_name"] for r in conn.execute("SELECT * FROM neuromorphic_boundary_contract_v05")]
    for required in ["no_hardware_truth_claim", "no_source_fact_rewrite", "p_r_before_xi", "no_direct_device_to_p", "no_direct_device_to_r", "no_direct_device_to_xi", "semantic_label_free"]:
        check(f"boundary_contract_{required}", required in contracts, contracts, f"contains {required}")
    check("contracts_active", conn.execute("SELECT COUNT(*) FROM neuromorphic_boundary_contract_v05 WHERE status != 'active'").fetchone()[0] == 0, "all active", "active")

    # Inherited boundaries remain intact.
    if table_exists(conn, "online_xi_boundary_tick_v03"):
        check("v03_no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all zero", "0")
        check("v03_no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM online_xi_boundary_tick_v03 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all zero", "0")
    if table_exists(conn, "xi_boundary_guard_v022"):
        check("v022_no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all zero", "0")
        check("v022_no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all zero", "0")

    check("artifact_manifest_present", count(conn, "neuromorphic_artifact_manifest_v05") >= 2, count(conn, "neuromorphic_artifact_manifest_v05"), ">=2")

    # Store acceptance rows.
    run_id = m["neuromorphic_run_id"] if m else "missing"
    conn.execute("DELETE FROM neuromorphic_acceptance_report_v05")
    tnow = now()
    for t in tests:
        conn.execute(
            "INSERT INTO neuromorphic_acceptance_report_v05 VALUES (?,?,?,?,?,?,?)",
            ("accv05_" + t["test_name"][:80], run_id, t["test_name"], "PASS" if t["passed"] else "FAIL", json.dumps(t["observed"], ensure_ascii=False, default=str), json.dumps(t["expected"], ensure_ascii=False, default=str), tnow),
        )
    conn.commit()
    stored = conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) FROM neuromorphic_acceptance_report_v05").fetchone()
    check("stored_acceptance_all_pass", stored[0] == stored[1] and stored[0] > 0, f"{stored[1]}/{stored[0]}", "all pass")

    passed = sum(1 for t in tests if t["passed"])
    total = len(tests)
    for t in tests:
        print(f"{'PASS' if t['passed'] else 'FAIL'} {t['test_name']}: observed={t['observed']} expected={t['expected']}")
    print(f"device_neutral_preneural_edge_v0.5 acceptance: {passed}/{total} PASS")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "total": total, "results": tests}, f, ensure_ascii=False, indent=2)
    conn.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
