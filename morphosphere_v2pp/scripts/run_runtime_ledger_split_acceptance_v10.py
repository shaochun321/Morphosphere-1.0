#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3
from pathlib import Path

RUN_ID = "runtime_ledger_split_v10"
CHECKS = []

def add(name, passed, observed, expected, severity="critical"):
    CHECKS.append((name, bool(passed), observed, expected, severity))

def file_sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("db")
    args=ap.parse_args()
    con=sqlite3.connect(args.db)
    con.row_factory=sqlite3.Row
    cur=con.cursor()
    def count(t):
        return cur.execute(f"select count(*) from {t}").fetchone()[0]
    # core tables
    required = [
        "runtime_ledger_split_run_manifest_v10",
        "runtime_store_manifest_v10",
        "runtime_chunk_index_v10",
        "runtime_tensor_summary_v10",
        "runtime_source_fact_digest_v10",
        "external_physical_adapter_contract_v10",
        "external_runtime_adapter_trial_v10",
        "runtime_ledger_boundary_contract_v10",
        "promotion_loop_policy_v10",
        "frozen_profile_candidate_v10",
        "runtime_ledger_acceptance_report_v10",
        "runtime_artifact_manifest_v10",
    ]
    tables = {r[0] for r in cur.execute("select name from sqlite_master where type='table'")}
    for t in required:
        add(f"table_exists_{t}", t in tables, t in tables, True)

    manifest = cur.execute("select * from runtime_ledger_split_run_manifest_v10 where run_id=?", (RUN_ID,)).fetchone()
    add("manifest_exists", manifest is not None, manifest is not None, True)
    if manifest:
        add("scientific_run_false", manifest["scientific_run"] == 0, manifest["scientific_run"], 0)
        add("sqlite_ledger_only", manifest["ledger_role"] == "sqlite_ledger_only_not_runtime_engine", manifest["ledger_role"], "sqlite_ledger_only_not_runtime_engine")
        add("hot_swap_disabled_in_manifest", manifest["hot_swap_allowed"] == 0, manifest["hot_swap_allowed"], 0)
        add("candidate_auto_apply_disabled_in_manifest", manifest["candidate_auto_apply_allowed"] == 0, manifest["candidate_auto_apply_allowed"], 0)

    add("runtime_store_manifest_count", count("runtime_store_manifest_v10") >= 4, count("runtime_store_manifest_v10"), ">=4")
    add("runtime_chunk_index_count", count("runtime_chunk_index_v10") >= 4, count("runtime_chunk_index_v10"), ">=4")
    add("runtime_tensor_summary_count", count("runtime_tensor_summary_v10") >= 2, count("runtime_tensor_summary_v10"), ">=2")
    add("source_fact_digest_count", count("runtime_source_fact_digest_v10") >= 10, count("runtime_source_fact_digest_v10"), ">=10")
    add("external_adapter_contracts", count("external_physical_adapter_contract_v10") >= 3, count("external_physical_adapter_contract_v10"), ">=3")

    # Validate artifact files sha if relative paths still accessible from package root.
    db_path = Path(args.db).resolve()
    root = db_path.parents[1] if db_path.parent.name == "outputs" else Path.cwd()
    mismatches = []
    for row in cur.execute("select relative_path,sha256 from runtime_store_manifest_v10"):
        p = (root / row["relative_path"]).resolve()
        if not p.exists() or file_sha(p) != row["sha256"]:
            mismatches.append(str(row["relative_path"]))
    add("runtime_store_sha_match", not mismatches, ",".join(mismatches) if mismatches else "all_match", "all_match")

    policy = cur.execute("select * from promotion_loop_policy_v10 limit 1").fetchone()
    add("promotion_policy_exists", policy is not None, policy is not None, True)
    if policy:
        add("promotion_hot_swap_blocked", policy["hot_swap_allowed"] == 0, policy["hot_swap_allowed"], 0)
        add("promotion_frozen_profile_required", policy["frozen_profile_required"] == 1, policy["frozen_profile_required"], 1)
        add("promotion_real_data_required", policy["real_external_data_required"] == 1, policy["real_external_data_required"], 1)
        add("promotion_human_review_required", policy["human_review_required"] == 1, policy["human_review_required"], 1)
        add("promotion_source_rewrite_blocked", policy["source_fact_rewrite_allowed"] == 0, policy["source_fact_rewrite_allowed"], 0)

    cand = cur.execute("select * from frozen_profile_candidate_v10 limit 1").fetchone()
    add("candidate_not_auto_applied", cand is not None and cand["auto_applied"] == 0, cand["auto_applied"] if cand else None, 0)
    add("candidate_manual_review_required", cand is not None and cand["manual_review_required"] == 1, cand["manual_review_required"] if cand else None, 1)

    trial = cur.execute("select quality_gate_status from external_runtime_adapter_trial_v10 limit 1").fetchone()
    add("external_gate_explicit", trial is not None and len(trial["quality_gate_status"]) > 0, trial["quality_gate_status"] if trial else None, "non_empty")

    passed=sum(1 for _,p,_,_,_ in CHECKS if p)
    total=len(CHECKS)
    print(f"runtime_ledger_split_v1.0 acceptance: {passed} / {total} PASS")
    for name,p,obs,exp,severity in CHECKS:
        print(f"{name}: {'PASS' if p else 'FAIL'} observed={obs} expected={exp}")
    return 0 if passed==total else 1

if __name__=="__main__":
    raise SystemExit(main())
