#!/usr/bin/env python3
import sqlite3, sys

def count(cur, table):
    return cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

def main(db):
    con=sqlite3.connect(db); cur=con.cursor(); checks=[]
    def add(name, ok, obs, exp): checks.append((name, ok, obs, exp))
    add('sqlite_openable', True, 'openable', 'openable')
    for t in ['streaming_queue_run_manifest_v14','streaming_queue_event_v14','queue_to_sensorium_dispatch_v14','queue_pr_xi_response_v14','streaming_queue_replay_result_v14','streaming_queue_acceptance_report_v14']:
        try: c=count(cur,t)
        except Exception: c=-1
        add(f'{t}_present', c>0, c, '>0')
    q=count(cur,'streaming_queue_event_v14'); d=count(cur,'queue_to_sensorium_dispatch_v14')
    add('queue_events_640', q==640, q, 640)
    add('dispatch_nonzero', d>0, d, '>0')
    max_depth=cur.execute('SELECT MAX(queue_depth_after) FROM streaming_queue_tick_state_v14').fetchone()[0]
    cap=cur.execute('SELECT queue_capacity FROM streaming_queue_config_v14 LIMIT 1').fetchone()[0]
    add('queue_bounded', max_depth<=cap, max_depth, f'<= {cap}')
    semantic=cur.execute('SELECT COUNT(*) FROM streaming_queue_event_v14 WHERE semantic_label IS NOT NULL').fetchone()[0]
    add('semantic_label_free', semantic==0, semantic, 0)
    rewrites=cur.execute('SELECT COUNT(*) FROM streaming_queue_drop_compensation_v14 WHERE source_fact_rewritten != 0').fetchone()[0]
    add('no_compensation_fact_rewrite', rewrites==0, rewrites, 0)
    replay_fail=cur.execute('SELECT COUNT(*) FROM streaming_queue_replay_result_v14 WHERE passed != 1').fetchone()[0]
    add('replay_all_passed', replay_fail==0, replay_fail, 0)
    stored_fail=cur.execute("SELECT COUNT(*) FROM streaming_queue_acceptance_report_v14 WHERE status != 'PASS'").fetchone()[0]
    add('stored_acceptance_all_passed', stored_fail==0, stored_fail, 0)
    passed=sum(1 for _,ok,_,_ in checks if ok)
    for name, ok, obs, exp in checks: print(f'{name}: {"PASS" if ok else "FAIL"} (observed={obs}, expected={exp})')
    print(f'streaming_queue_v1.4 acceptance: {passed} / {len(checks)} PASS')
    sys.exit(0 if passed==len(checks) else 1)
if __name__=='__main__':
    if len(sys.argv)!=2:
        print('usage: run_streaming_queue_acceptance_v14.py <db>'); sys.exit(2)
    main(sys.argv[1])
