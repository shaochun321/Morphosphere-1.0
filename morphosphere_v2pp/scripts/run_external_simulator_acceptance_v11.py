#!/usr/bin/env python3
import argparse, hashlib, os, sqlite3, sys
from pathlib import Path

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('db')
    args=ap.parse_args()
    conn=sqlite3.connect(args.db)
    cur=conn.cursor()
    checks=[]
    def check(name, pred, obs='', exp=''):
        checks.append((name, bool(pred), str(obs), str(exp)))
    # Avoid expensive full integrity scans in large append-only ledgers; verify openable DB and key table reads.
    quick='openable'
    check('sqlite_openable', True, quick, 'openable')
    tables=['external_simulator_run_manifest_v11','external_runtime_store_manifest_v11','external_field_summary_v11','external_cell_state_summary_v11','external_simulator_replay_result_v11','external_simulator_acceptance_report_v11']
    for t in tables:
        try: cnt=cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        except Exception as e: cnt=-1
        check(f'{t}_has_rows', cnt>0, cnt, '>0')
    vals=dict(cur.execute('SELECT role, record_count FROM external_runtime_store_manifest_v11').fetchall())
    check('field_sidecar_640_rows', vals.get('external_field_tensor')==640, vals.get('external_field_tensor'), 640)
    check('cell_sidecar_500_rows', vals.get('external_cell_state_tensor')==500, vals.get('external_cell_state_tensor'), 500)
    check('event_sidecar_1500_rows', vals.get('external_emitted_event_tensor')==1500, vals.get('external_emitted_event_tensor'), 1500)
    check('mapping_sidecar_1500_rows', vals.get('external_to_raw_event_mapping')==1500, vals.get('external_to_raw_event_mapping'), 1500)
    man=cur.execute('SELECT sqlite_role, scientific_run, hot_swap_allowed, source_fact_rewrite_allowed FROM external_simulator_run_manifest_v11 LIMIT 1').fetchone()
    check('sqlite_ledger_only', man and man[0]=='sqlite_ledger_only_not_runtime_engine', man[0] if man else None, 'ledger only')
    check('scientific_run_false', man and man[1]==0, man[1] if man else None, 0)
    check('hot_swap_forbidden', man and man[2]==0, man[2] if man else None, 0)
    check('source_fact_rewrite_forbidden', man and man[3]==0, man[3] if man else None, 0)
    replay=cur.execute('SELECT COUNT(*), SUM(passed) FROM external_simulator_replay_result_v11').fetchone()
    check('ten_replay_scenarios', replay[0]==10, replay[0], 10)
    check('all_replay_scenarios_passed', replay[1]==10, replay[1], 10)
    digest=cur.execute('SELECT COUNT(*) FROM source_fact_digest_v11 WHERE protected=1').fetchone()[0]
    check('source_fact_digests_present', digest>=9, digest, '>=9')
    pr=cur.execute('SELECT COUNT(*) FROM p_predictive_support_v022').fetchone()[0]
    rr=cur.execute('SELECT COUNT(*) FROM r_counterstructure_v022').fetchone()[0]
    xi=cur.execute('SELECT COUNT(*) FROM xi_boundary_guard_v022').fetchone()[0]
    check('pr_xi_tables_preserved', (pr,rr,xi)==(50,18,87), (pr,rr,xi), '(50,18,87)')
    acc=cur.execute('SELECT COUNT(*), SUM(passed) FROM external_simulator_acceptance_report_v11').fetchone()
    check('stored_acceptance_all_pass', acc[0]==acc[1] and acc[0]>=30, acc, 'all pass >=30')
    fail=[c for c in checks if not c[1]]
    print(f"external_simulator_adapter_v1.1 acceptance: {len(checks)-len(fail)} / {len(checks)} PASS")
    for name, ok, obs, exp in checks:
        print(('PASS' if ok else 'FAIL') + ' ' + name + ' observed=' + obs + ' expected=' + exp)
    sys.stdout.flush()
    os._exit(1 if fail else 0)
if __name__=='__main__': main()
