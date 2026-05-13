#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

REQUIRED = [
    "historical_issue_register_v022",
    "layer_interface_contract_v022",
    "layer_port_contract_v022",
    "pr_term_registry_v022",
    "o_candidate_bridge_v022",
    "p_predictive_support_v022",
    "r_counterstructure_v022",
    "xi_boundary_guard_v022",
    "pr_decomposition_binding_v022",
    "external_ledger_status_v022",
    "pr_restoration_run_manifest_v022",
    "pr_restoration_acceptance_report_v022",
]
SOURCE_FACTS = [
    "spacetime_cell",
    "information_fiber",
    "raw_event_stream",
    "cell_spatial_coordinate_snapshot",
    "information_relative_coordinate_snapshot",
    "preneural_node_state",
    "dynamic_origin_anchor_state",
    "dynamic_latent_trajectory_state",
    "xin_residue_dynamics",
    "system_clock_entry",
]
EXTERNAL = [
    "external_entropy_ledger",
    "external_conserved_quantity_ledger",
    "external_dissipation_ledger",
    "external_noise_budget_ledger",
    "external_anomaly_ledger",
    "external_isolation_report",
]


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

    def check(name, cond, observed, expected):
        tests.append({"test_name": name, "passed": bool(cond), "observed": observed, "expected": expected})

    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in REQUIRED:
        check(f"table_exists_{table}", table in tables, table in tables, "exists")

    manifest = conn.execute("SELECT * FROM pr_restoration_run_manifest_v022 ORDER BY created_at DESC LIMIT 1").fetchone()
    check("manifest_exists", manifest is not None, "present" if manifest else "missing", "present")
    if manifest:
        check("execution_mode_append_only", manifest["execution_mode"] == "diagnostic_append_only_pr_restoration", manifest["execution_mode"], "diagnostic_append_only_pr_restoration")
        check("not_scientific_run", manifest["scientific_run"] == 0, manifest["scientific_run"], "0")
        check("semantic_labels_disallowed", manifest["semantic_labels_allowed"] == 0, manifest["semantic_labels_allowed"], "0")
        before = json.loads(manifest["source_fact_counts_before_json"])
        after = json.loads(manifest["source_fact_counts_after_json"])
        live = {t: count(conn, t) for t in SOURCE_FACTS}
        check("source_fact_counts_unchanged_in_manifest", before == after, after, "same as before")
        check("live_source_fact_counts_match_manifest", live == after, live, "manifest after counts")
        check("open_issues_retained", manifest["open_issue_count"] >= 3, manifest["open_issue_count"], ">=3")
        check("interfaces_declared", manifest["interface_contract_count"] >= 12, manifest["interface_contract_count"], ">=12")
        check("o_bridge_count_positive", manifest["o_bridge_count"] > 0, manifest["o_bridge_count"], ">0")
        check("p_support_count_matches_o", manifest["p_support_count"] == manifest["o_bridge_count"], {"P": manifest["p_support_count"], "O": manifest["o_bridge_count"]}, "P = O")
        check("r_counter_count_positive", manifest["r_counter_count"] > 0, manifest["r_counter_count"], ">0")
        check("xi_guard_count_positive", manifest["xi_guard_count"] > 0, manifest["xi_guard_count"], ">0")

    r = conn.execute("SELECT canonical_name, role_definition FROM pr_term_registry_v022 WHERE symbol='R'").fetchone()
    xi = conn.execute("SELECT canonical_name, role_definition FROM pr_term_registry_v022 WHERE symbol='Xi/Xin'").fetchone()
    check("R_is_counterstructure_not_residual", r is not None and "Counter-Structure" in r["canonical_name"] and "Residual" not in r["canonical_name"], dict(r) if r else None, "R canonical_name contains Counter-Structure and not Residual")
    check("Xi_is_residue_carrier", xi is not None and "Residue" in xi["canonical_name"], dict(xi) if xi else None, "Xi/Xin canonical_name contains Residue")

    check("no_xi_direct_to_p", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_p_allowed != 0").fetchone()[0] == 0, "all forbidden", "0 allowed")
    check("no_xi_direct_to_r", conn.execute("SELECT COUNT(*) FROM xi_boundary_guard_v022 WHERE direct_to_r_allowed != 0").fetchone()[0] == 0, "all forbidden", "0 allowed")
    check("all_R_rows_forbid_equivalence_to_Xi", count(conn, "r_counterstructure_v022") == conn.execute("SELECT COUNT(*) FROM r_counterstructure_v022 WHERE forbidden_equivalence LIKE '%not Xi/Xin%'").fetchone()[0], count(conn, "r_counterstructure_v022"), "all R rows include forbidden equivalence")
    check("chain_order_contracts_present", conn.execute("SELECT COUNT(*) FROM layer_interface_contract_v022 WHERE interface_name IN ('trace_to_o_candidate','o_candidate_to_p','o_candidate_to_r','pr_to_xi_boundary')").fetchone()[0] == 4, "present", "4 contracts")
    check("external_ledgers_populated", all(count(conn, t) > 0 for t in EXTERNAL), {t: count(conn, t) for t in EXTERNAL}, "all > 0")
    check("external_ledger_status_reported", count(conn, "external_ledger_status_v022") >= len(EXTERNAL), count(conn, "external_ledger_status_v022"), ">=6")
    check("legacy_pr_graph_kept_separate", count(conn, "pr_confirmation_graph_record") > 0 and count(conn, "p_predictive_support_v022") > 0, {"legacy": count(conn, "pr_confirmation_graph_record"), "new_P": count(conn, "p_predictive_support_v022")}, "legacy and restored tables both present")
    stored = conn.execute("SELECT COUNT(*), SUM(CASE WHEN status='PASS' THEN 1 ELSE 0 END) FROM pr_restoration_acceptance_report_v022").fetchone()
    check("stored_acceptance_all_pass", stored[0] > 0 and stored[0] == stored[1], f"{stored[1]}/{stored[0]}", "all pass")

    passed = sum(1 for t in tests if t["passed"])
    total = len(tests)
    for t in tests:
        print(f"{'PASS' if t['passed'] else 'FAIL'} {t['test_name']}: observed={t['observed']} expected={t['expected']}")
    print(f"pr_restoration_v0.2.2 acceptance: {passed}/{total} PASS")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"passed": passed, "total": total, "results": tests}, f, ensure_ascii=False, indent=2)
    conn.close()
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
