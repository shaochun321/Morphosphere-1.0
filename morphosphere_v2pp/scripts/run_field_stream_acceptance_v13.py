#!/usr/bin/env python3
"""Acceptance checks for field_stream_reader_sensorium_adapter_v1.3."""
import argparse, sqlite3, sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('db'); args=ap.parse_args()
    conn=sqlite3.connect(args.db); cur=conn.cursor()
    checks=[]
    def add(name, cond, detail=''):
        checks.append((name, bool(cond), detail))
    add('quick_check_ok', cur.execute('PRAGMA quick_check').fetchone()[0]=='ok')
    for table,min_count in [('field_chunk_reader_manifest_v13',10),('field_stream_event_v13',640),('field_stream_to_sensorium_bridge_v13',640),('streaming_pr_response_v13',50),('field_stream_replay_result_v13',8),('runtime_reader_boundary_contract_v13',4)]:
        cnt=cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        add(table+'_count', cnt>=min_count, f'{cnt} >= {min_count}')
    fail=cur.execute('SELECT COUNT(*) FROM field_stream_acceptance_report_v13 WHERE passed=0').fetchone()[0]
    add('stored_acceptance_all_passed', fail==0, f'failed={fail}')
    hot=cur.execute("SELECT value FROM field_stream_run_manifest_v13 WHERE key='hot_swap_allowed'").fetchone()[0]
    add('hot_swap_forbidden', hot=='false')
    sem=cur.execute("SELECT value FROM field_stream_run_manifest_v13 WHERE key='semantic_labels_allowed'").fetchone()[0]
    add('semantic_label_free', sem=='false')
    prxi=cur.execute("SELECT value FROM field_stream_run_manifest_v13 WHERE key='p_r_before_xi'").fetchone()[0]
    add('p_r_before_xi', prxi=='true')
    srcfail=cur.execute("SELECT COUNT(*) FROM source_fact_digest_v13 WHERE status!='PASS'").fetchone()[0]
    add('source_facts_available', srcfail==0, f'source digest failures={srcfail}')
    verdicts=cur.execute('SELECT COUNT(DISTINCT verdict) FROM streaming_pr_response_v13').fetchone()[0]
    add('pr_verdict_diversity', verdicts>=2, f'verdicts={verdicts}')
    base=cur.execute("SELECT xi_pressure_proxy FROM field_stream_replay_result_v13 WHERE scenario_name='baseline_stream_reader'").fetchone()[0]
    noise=cur.execute("SELECT xi_pressure_proxy FROM field_stream_replay_result_v13 WHERE scenario_name='stream_noise_30'").fetchone()[0]
    add('noise_increases_xi', noise>base, f'{noise} > {base}')
    passed=sum(1 for _,ok,_ in checks if ok)
    for name,ok,detail in checks:
        print(f'{name}: {"PASS" if ok else "FAIL"} {detail}')
    print(f'field_stream_reader_v1.3 acceptance: {passed} / {len(checks)} PASS')
    sys.exit(0 if passed==len(checks) else 1)
if __name__=='__main__': main()
