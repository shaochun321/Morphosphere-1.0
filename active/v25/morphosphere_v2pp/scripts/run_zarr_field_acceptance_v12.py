#!/usr/bin/env python3
"""Acceptance checks for v1.2 Zarr/HDF5 field runtime adapter."""
import json, sqlite3, sys
from pathlib import Path

def count(conn,t): return conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
def main():
    if len(sys.argv)<2: raise SystemExit("usage: run_zarr_field_acceptance_v12.py <db>")
    db=Path(sys.argv[1]); root=Path.cwd(); conn=sqlite3.connect(str(db)); checks=[]
    def ck(n,ok,obs,exp): checks.append((n,ok,obs,exp))
    ck("db_openable", db.exists(), db, "exists")
    qc=conn.execute("PRAGMA quick_check").fetchone()[0]; ck("sqlite_quick_check", qc=="ok", qc, "ok")
    tables=["zarr_field_run_manifest_v12","zarr_store_manifest_v12","zarr_array_manifest_v12","zarr_chunk_index_v12","zarr_field_summary_v12","zarr_event_projection_summary_v12","hdf5_adapter_contract_v12","zarr_replay_result_v12","runtime_storage_boundary_contract_v12","source_fact_digest_v12","zarr_field_acceptance_report_v12","zarr_field_artifact_manifest_v12"]
    for t in tables:
        exists=conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone()[0]==1
        ck(f"table_exists_{t}", exists, exists, True)
        if exists: ck(f"table_nonempty_{t}", count(conn,t)>0, count(conn,t), ">0")
    m=conn.execute("SELECT hdf5_status,sqlite_role,hot_swap_allowed,source_fact_rewrite_allowed,scientific_run FROM zarr_field_run_manifest_v12 LIMIT 1").fetchone()
    ck("manifest_present", m is not None, m, "present")
    if m:
        ck("hdf5_contract_only", m[0]=="contract_only_not_materialized", m[0], "contract_only_not_materialized")
        ck("sqlite_ledger_only", m[1]=="sqlite_ledger_only_not_runtime_engine", m[1], "sqlite_ledger_only_not_runtime_engine")
        ck("hot_swap_forbidden", m[2]==0, m[2], 0); ck("source_rewrite_forbidden", m[3]==0, m[3], 0); ck("not_scientific_run", m[4]==0, m[4], 0)
    arr=conn.execute("SELECT shape_json,channel_names_json FROM zarr_array_manifest_v12 LIMIT 1").fetchone()
    if arr:
        shape=json.loads(arr[0]); channels=json.loads(arr[1])
        ck("shape_rank_5", len(shape)==5, shape, "rank 5")
        ck("channel_count_5", len(channels)==5, channels, 5)
        ck("chunk_count_matches_time", count(conn,"zarr_chunk_index_v12")==shape[0], count(conn,"zarr_chunk_index_v12"), shape[0])
        ck("summary_count_matches", count(conn,"zarr_field_summary_v12")==shape[0]*len(channels), count(conn,"zarr_field_summary_v12"), shape[0]*len(channels))
    artifact_paths=[r[0] for r in conn.execute("SELECT relative_path FROM zarr_field_artifact_manifest_v12")]
    existing=sum(1 for rel in artifact_paths if (root/rel).exists())
    ck("artifact_paths_exist", existing==len(artifact_paths), existing, len(artifact_paths))
    replay=conn.execute("SELECT COUNT(*),SUM(passed),MAX(source_fact_rewritten) FROM zarr_replay_result_v12").fetchone()
    ck("replay_scenarios_present", replay[0]>=7, replay[0], ">=7")
    ck("all_replay_passed", replay[1]==replay[0], replay[1], replay[0])
    ck("no_replay_source_rewrite", replay[2]==0, replay[2], 0)
    stored=conn.execute("SELECT COUNT(*),SUM(passed) FROM zarr_field_acceptance_report_v12").fetchone()
    ck("stored_acceptance_all_pass", stored[0]==stored[1], stored, "all pass")
    conn.close()
    passed=sum(1 for _,ok,_,_ in checks if ok); total=len(checks)
    for n,ok,obs,exp in checks: print(f"{n}: {'PASS' if ok else 'FAIL'} observed={obs} expected={exp}")
    print(f"zarr_field_runtime_adapter_v1.2 acceptance: {passed} / {total} PASS")
    if passed!=total: raise SystemExit(1)
if __name__=="__main__": main()
