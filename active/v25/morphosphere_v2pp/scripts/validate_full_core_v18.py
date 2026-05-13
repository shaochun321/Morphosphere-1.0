#!/usr/bin/env python3
import json, os, pathlib, sqlite3, sys
root = pathlib.Path(__file__).resolve().parents[2]
db_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'outputs' / 'morphosphere_full_core_v18_output_database.db'
if not db_path.is_absolute():
    db_path = root / db_path
checks=[]
def add(name, ok, obs='', exp=''):
    checks.append((name, bool(ok), obs, exp))
add('core_src_present', (root/'morphosphere_v2pp/src').is_dir(), 'exists' if (root/'morphosphere_v2pp/src').is_dir() else 'missing', 'exists')
add('migrations_present', (root/'morphosphere_v2pp/migrations').is_dir(), 'exists' if (root/'morphosphere_v2pp/migrations').is_dir() else 'missing', 'exists')
add('runtime_v12_zarr_present', (root/'runtime_store/v12/field_store_v12.zarr').is_dir(), 'exists' if (root/'runtime_store/v12/field_store_v12.zarr').is_dir() else 'missing', 'exists')
for v in ['v13','v14','v15','v16','v17','v18']:
    add(f'runtime_{v}_present', (root/f'runtime_store/{v}').is_dir(), 'exists' if (root/f'runtime_store/{v}').is_dir() else 'missing', 'exists')
add('latest_db_present', db_path.exists(), str(db_path), 'exists')
if db_path.exists():
    con=sqlite3.connect(str(db_path), timeout=10)
    def count(table):
        return con.execute(f"select count(*) from {table}").fetchone()[0]
    required_tables = [
        'sandbox_profile_registry_v18','sandbox_replay_scenario_v18','sandbox_profile_metric_v18','sandbox_decision_v18',
        'frozen_promotion_run_manifest_v17','sensor_fusion_memory_run_manifest_v16','multirate_sync_run_manifest_v15',
        'field_stream_run_manifest_v13'
    ]
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    for t in required_tables:
        add(f'table_{t}', t in tables, 'present' if t in tables else 'missing', 'present')
    if 'sandbox_profile_registry_v18' in tables:
        add('v18_profiles', count('sandbox_profile_registry_v18') >= 2, count('sandbox_profile_registry_v18'), '>=2')
    if 'sandbox_replay_scenario_v18' in tables:
        add('v18_replay_scenarios', count('sandbox_replay_scenario_v18') >= 10, count('sandbox_replay_scenario_v18'), '>=10')
    if 'sandbox_decision_v18' in tables:
        row=con.execute('select candidate_promoted, auto_applied, manual_review_required from sandbox_decision_v18').fetchone()
        add('candidate_not_promoted', row and row[0]==0, row, 'candidate_promoted=0')
        add('candidate_not_auto_applied', row and row[1]==0, row, 'auto_applied=0')
        add('manual_review_required', row and row[2]==1, row, 'manual_review_required=1')
    con.close()
passed=sum(1 for _,ok,_,_ in checks if ok)
for name,ok,obs,exp in checks:
    print(f"{name}: {'PASS' if ok else 'FAIL'} observed={obs} expected={exp}")
print(f"full_core_v1.8 deployment sanity: {passed} / {len(checks)} PASS")
sys.exit(0 if passed==len(checks) else 1)
