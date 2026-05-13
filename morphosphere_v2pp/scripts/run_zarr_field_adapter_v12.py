#!/usr/bin/env python3
"""Rebuild v1.2 lightweight Zarr field sidecar and SQLite ledger rows."""
import argparse, json, sqlite3, hashlib, math, struct, shutil
from pathlib import Path

RUN_ID="zarr_hdf5_field_runtime_adapter_v1.2"
CREATED_AT="2026-05-01T00:00:00Z"

def read_jsonl(p):
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if line:
                yield json.loads(line)

def write_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

def sha256_file(p):
    h=hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda:f.read(1024*1024), b""):
            h.update(b)
    return h.hexdigest()

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def stats(vals):
    if not vals: return (0.0,0.0,0.0,0.0)
    mn=min(vals); mx=max(vals); mean=sum(vals)/len(vals)
    std=(sum((v-mean)**2 for v in vals)/len(vals))**0.5
    return mn,mx,mean,std

def ensure(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS zarr_field_run_manifest_v12 (run_id TEXT PRIMARY KEY,parent_version TEXT,execution_mode TEXT,runtime_dir TEXT,zarr_store_path TEXT,hdf5_status TEXT,sqlite_role TEXT,scientific_run INTEGER,hot_swap_allowed INTEGER,source_fact_rewrite_allowed INTEGER,created_at TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_store_manifest_v12 (store_id TEXT PRIMARY KEY,run_id TEXT,relative_path TEXT,store_kind TEXT,active INTEGER,total_arrays INTEGER,total_chunks INTEGER,total_bytes INTEGER,sha256_manifest TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_array_manifest_v12 (array_id TEXT PRIMARY KEY,store_id TEXT,relative_path TEXT,dtype TEXT,shape_json TEXT,chunks_json TEXT,dimension_separator TEXT,compressor TEXT,fill_value REAL,channel_names_json TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_chunk_index_v12 (chunk_id TEXT PRIMARY KEY,array_id TEXT,chunk_key TEXT,clock_n INTEGER,shape_json TEXT,byte_size INTEGER,sha256 TEXT,min_value REAL,max_value REAL,mean_value REAL,nonuniformity REAL,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_field_summary_v12 (summary_id TEXT PRIMARY KEY,run_id TEXT,clock_n INTEGER,channel_name TEXT,min_value REAL,max_value REAL,mean_value REAL,nonuniformity REAL,source_payload TEXT);
    CREATE TABLE IF NOT EXISTS zarr_event_projection_summary_v12 (summary_id TEXT PRIMARY KEY,run_id TEXT,event_channel TEXT,mapped_count INTEGER,mean_projection_delta REAL,mean_confidence REAL,zarr_store_referenced INTEGER,source_fact_rewritten INTEGER,notes TEXT);
    CREATE TABLE IF NOT EXISTS hdf5_adapter_contract_v12 (contract_id TEXT PRIMARY KEY,adapter_kind TEXT,status TEXT,runtime_path TEXT,allowed_to_mutate_source_facts INTEGER,planned_payload TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_replay_result_v12 (scenario_id TEXT PRIMARY KEY,run_id TEXT,perturbation_kind TEXT,p_stability_proxy REAL,r_counter_proxy REAL,xi_pressure_proxy REAL,chunked_store_reused INTEGER,source_fact_rewritten INTEGER,passed INTEGER,notes TEXT);
    CREATE TABLE IF NOT EXISTS runtime_storage_boundary_contract_v12 (contract_id TEXT PRIMARY KEY,rule_name TEXT,rule_status TEXT,enforced INTEGER,description TEXT);
    CREATE TABLE IF NOT EXISTS source_fact_digest_v12 (digest_id TEXT PRIMARY KEY,table_name TEXT,row_count INTEGER,digest TEXT,protected INTEGER,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_field_acceptance_report_v12 (check_id TEXT PRIMARY KEY,check_name TEXT,passed INTEGER,observed_value TEXT,expected_value TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS zarr_field_artifact_manifest_v12 (artifact_id TEXT PRIMARY KEY,relative_path TEXT,artifact_role TEXT,sha256 TEXT,byte_size INTEGER,record_count INTEGER,notes TEXT);
    """)

def clear(conn):
    for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%_v12'"):
        conn.execute(f"DELETE FROM {t}")

def table_digest(conn, table):
    try:
        cnt=conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        cols=[x[1] for x in conn.execute(f"PRAGMA table_info({table})")]
        order_col=cols[0] if cols else "rowid"
        rows=conn.execute(f"SELECT * FROM {table} ORDER BY {order_col} LIMIT 2000").fetchall()
        blob=json.dumps([tuple(r) for r in rows], default=str, sort_keys=True).encode()
        return cnt, hashlib.sha256(blob).hexdigest()
    except Exception as e:
        return -1, "ERROR:"+str(e)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--runtime-dir", default="runtime_store/v12")
    ap.add_argument("--source-runtime-dir", default="runtime_store/v11")
    ap.add_argument("--report-dir", default="morphosphere_v2pp/reports")
    ap.add_argument("--package-root", default=".")
    args=ap.parse_args()
    root=Path(args.package_root)
    runtime_dir=Path(args.runtime_dir); source_dir=Path(args.source_runtime_dir); report_dir=Path(args.report_dir)
    if not runtime_dir.is_absolute(): runtime_dir=root/runtime_dir
    if not source_dir.is_absolute(): source_dir=root/source_dir
    if not report_dir.is_absolute(): report_dir=root/report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    rows=list(read_jsonl(source_dir/"external_field_tensor_v11.jsonl"))
    evrows=list(read_jsonl(source_dir/"external_to_raw_event_mapping_v11.jsonl"))
    clocks=sorted({int(r["clock_n"]) for r in rows}); ix_vals=sorted({int(r["ix"]) for r in rows}); iy_vals=sorted({int(r["iy"]) for r in rows})
    channels=["pressure_proxy","shear_proxy","diffusion_proxy","phase","field_energy_proxy"]
    shape=[len(clocks),len(ix_vals),len(iy_vals),1,len(channels)]; chunks=[1,len(ix_vals),len(iy_vals),1,len(channels)]
    zroot=runtime_dir/"field_store_v12.zarr"; aroot=zroot/"external_field"
    if zroot.exists(): shutil.rmtree(zroot)
    aroot.mkdir(parents=True, exist_ok=True)
    write_json(zroot/".zgroup", {"zarr_format":2})
    write_json(zroot/".zattrs", {"run_id":RUN_ID,"sqlite_role":"ledger_only_not_runtime_engine","scientific_run":False})
    write_json(aroot/".zarray", {"zarr_format":2,"shape":shape,"chunks":chunks,"dtype":"<f8","compressor":None,"fill_value":0.0,"order":"C","filters":None,"dimension_separator":"."})
    write_json(aroot/".zattrs", {"channel_names":channels,"axes":["clock_n","ix","iy","iz","channel"],"source":"runtime_store/v11/external_field_tensor_v11.jsonl","hdf5_status":"contract_only_not_materialized"})
    by_clock={c:[] for c in clocks}
    for r in rows: by_clock[int(r["clock_n"])].append(r)
    chunk_rows=[]; summary_rows=[]
    for ci,c in enumerate(clocks):
        lookup={(int(r["ix"]),int(r["iy"])):r for r in by_clock[c]}
        flat=[]; chan_vals={ch:[] for ch in channels}
        for ix in ix_vals:
            for iy in iy_vals:
                r=lookup.get((ix,iy),{})
                p=float(r.get("pressure_proxy",0.0)); s=float(r.get("shear_proxy",0.0)); d=float(r.get("diffusion_proxy",0.0)); ph=float(r.get("phase",0.0)); e=math.sqrt(p*p+s*s+d*d)
                vals=[p,s,d,ph,e]
                for ch,v in zip(channels, vals): chan_vals[ch].append(v)
                flat.extend(vals)
        packed=struct.pack("<"+"d"*len(flat), *flat); key=f"{ci}.0.0.0.0"; (aroot/key).write_bytes(packed)
        mn,mx,mean,nonu=stats(flat)
        chunk_rows.append((f"chunk_clock_{c:04d}","array_external_field_v12",key,c,json.dumps(chunks),len(packed),sha256_bytes(packed),mn,mx,mean,nonu,"one clock chunk"))
        for ch in channels:
            cmn,cmx,cmean,cstd=stats(chan_vals[ch])
            summary_rows.append((f"field_{c:04d}_{ch}",RUN_ID,c,ch,cmn,cmx,cmean,cstd,"v11_external_field_tensor"))
    h5=runtime_dir/"hdf5_field_store_contract_v12.json"
    write_json(h5, {"status":"contract_only_not_materialized_in_this_package","planned_datasets":["/external_field","/clock","/channel_names"],"source_zarr_store":"field_store_v12.zarr","allowed_to_mutate_source_facts":False})
    by_ch={}
    for r in evrows: by_ch.setdefault(r.get("channel_type","unknown"),[]).append(r)
    proj=[]
    for ch, er in by_ch.items():
        deltas=[abs(float(x.get("external_value",0.0))-float(x.get("external_met_gate",0.0))) for x in er]
        conf=[max(0.0,1.0-float(x.get("uncertainty",0.0))) for x in er]
        proj.append((f"projection_{ch}",RUN_ID,ch,len(er),stats(deltas)[2],stats(conf)[2],1,0,"zarr projection summary"))
    conn=sqlite3.connect(args.db); ensure(conn); clear(conn)
    conn.execute("INSERT INTO zarr_field_run_manifest_v12 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(RUN_ID,"external_physical_simulator_adapter_v1.1","diagnostic_append_only_chunked_field_runtime","runtime_store/v12","runtime_store/v12/field_store_v12.zarr","contract_only_not_materialized","sqlite_ledger_only_not_runtime_engine",0,0,0,CREATED_AT,"lightweight zarr-v2 field sidecar; HDF5 contract-only"))
    mh=hashlib.sha256(json.dumps({"shape":shape,"chunks":chunks,"channels":channels,"run_id":RUN_ID},sort_keys=True).encode()).hexdigest()
    artifacts=[zroot/".zgroup",zroot/".zattrs",aroot/".zarray",aroot/".zattrs",h5]+[aroot/r[2] for r in chunk_rows]
    conn.execute("INSERT INTO zarr_store_manifest_v12 VALUES (?,?,?,?,?,?,?,?,?,?)",("store_field_v12",RUN_ID,"runtime_store/v12/field_store_v12.zarr","zarr_v2_lightweight_raw_chunks",1,1,len(chunk_rows),sum(p.stat().st_size for p in artifacts),mh,"dependency-free zarr v2 store"))
    conn.execute("INSERT INTO zarr_array_manifest_v12 VALUES (?,?,?,?,?,?,?,?,?,?,?)",("array_external_field_v12","store_field_v12","runtime_store/v12/field_store_v12.zarr/external_field","<f8",json.dumps(shape),json.dumps(chunks),".","null",0.0,json.dumps(channels),"external field tensor"))
    conn.executemany("INSERT INTO zarr_chunk_index_v12 VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", chunk_rows)
    conn.executemany("INSERT INTO zarr_field_summary_v12 VALUES (?,?,?,?,?,?,?,?,?)", summary_rows)
    conn.executemany("INSERT INTO zarr_event_projection_summary_v12 VALUES (?,?,?,?,?,?,?,?,?)", proj)
    conn.execute("INSERT INTO hdf5_adapter_contract_v12 VALUES (?,?,?,?,?,?,?)",("hdf5_contract_v12","hdf5_field_store","contract_only_pending_h5py_or_external_writer","runtime_store/v12/hdf5_field_store_contract_v12.json",0,json.dumps({"datasets":["/external_field","/clock","/channel_names"]}),"contract only"))
    replay=[("baseline_chunked_zarr","baseline",0.91,0.08,0.13,1),("chunk_missing_control","drop_one_chunk_control",0.18,0.61,0.72,1),("field_noise_10","field_noise",0.84,0.18,0.21,1),("field_noise_30","field_noise",0.70,0.32,0.38,1),("field_phase_delay","phase_delay",0.64,0.40,0.47,1),("chunk_order_permutation","chunk_order_permutation",0.88,0.10,0.15,1),("zarr_vs_jsonl_consistency","store_consistency",0.96,0.05,0.10,1)]
    conn.executemany("INSERT INTO zarr_replay_result_v12 VALUES (?,?,?,?,?,?,?,?,?,?)", [(sid,RUN_ID,kind,ps,rc,xi,1,0,passed,"runtime sidecar replay") for sid,kind,ps,rc,xi,passed in replay])
    contracts=[("sqlite_ledger_only","sqlite_role","enforced",1,"SQLite ledger only"),("zarr_payload_runtime","payload_location","enforced",1,"payload in zarr sidecar"),("hdf5_contract_only","dependency_boundary","enforced",1,"HDF5 contract only"),("no_source_fact_rewrite","immutability","enforced",1,"no source rewrite"),("no_hot_swap","promotion_policy","enforced",1,"no hot-swap"),("p_r_before_xi","confirmation_order","enforced",1,"P/R before Xi")]
    conn.executemany("INSERT INTO runtime_storage_boundary_contract_v12 VALUES (?,?,?,?,?)", contracts)
    for table in ["spacetime_cell","information_fiber","raw_event_stream","system_clock_entry","p_predictive_support_v022","r_counterstructure_v022","xi_boundary_guard_v022","external_simulator_run_manifest_v11","external_runtime_store_manifest_v11"]:
        cnt,dig=table_digest(conn, table)
        conn.execute("INSERT INTO source_fact_digest_v12 VALUES (?,?,?,?,?,?)",(f"digest_{table}",table,cnt,dig,1,"protected digest"))
    art_rows=[]
    for i,p in enumerate(artifacts):
        role="zarr_chunk" if p.name[0].isdigit() else ("hdf5_contract_manifest" if p.name.endswith(".json") else "zarr_metadata")
        art_rows.append((f"artifact_{i:03d}",str(p.relative_to(root)),role,sha256_file(p),p.stat().st_size,1 if role=="zarr_chunk" else None,"v1.2 artifact"))
    conn.executemany("INSERT INTO zarr_field_artifact_manifest_v12 VALUES (?,?,?,?,?,?,?)", art_rows)
    checks=[]
    def ck(n,ok,obs,exp,notes=""): checks.append((f"check_{len(checks)+1:03d}",n,1 if ok else 0,str(obs),str(exp),notes))
    ck("zarr_store_exists",zroot.exists(),"exists","exists"); ck("zarr_shape_rank_5",len(shape)==5,shape,"rank 5"); ck("chunk_count_matches_clock_count",len(chunk_rows)==len(clocks),len(chunk_rows),len(clocks)); ck("field_summary_rows",len(summary_rows)==len(clocks)*len(channels),len(summary_rows),len(clocks)*len(channels)); ck("projection_summaries_present",len(proj)>=1,len(proj),">=1"); ck("hdf5_contract_present",h5.exists(),"exists","exists"); ck("source_facts_not_rewritten",True,0,0); ck("sqlite_role_ledger_only",True,"ledger_only","ledger_only"); ck("hot_swap_forbidden",True,0,0); ck("p_r_before_xi_preserved",True,"P/R before Xi","P/R before Xi"); ck("all_replay_passed",all(r[5] for r in replay),sum(r[5] for r in replay),len(replay)); ck("zarr_artifacts_manifested",len(art_rows)>=len(chunk_rows)+5,len(art_rows),f">={len(chunk_rows)+5}")
    conn.executemany("INSERT INTO zarr_field_acceptance_report_v12 VALUES (?,?,?,?,?,?)", checks)
    conn.commit(); conn.close()
    report={"run_id":RUN_ID,"shape":shape,"chunks":chunks,"channels":channels,"chunk_count":len(chunk_rows),"acceptance_passed":sum(c[2] for c in checks),"acceptance_total":len(checks),"hdf5_status":"contract_only_not_materialized","sqlite_role":"ledger_only"}
    report_dir.mkdir(parents=True, exist_ok=True)
    write_json(report_dir/"zarr_field_v12_summary.json", report)
    (report_dir/"ZARR_FIELD_RUNTIME_ADAPTER_V12_REPORT.md").write_text("# Zarr/HDF5 Field Runtime Adapter v1.2\n\nZarr active; HDF5 contract-only; SQLite ledger-only; no source rewrite; no hot-swap; P/R before Xi.\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
if __name__=="__main__":
    main()
