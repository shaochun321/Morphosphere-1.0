#!/usr/bin/env python3
import sqlite3, argparse
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/v366/m366_build_pass13_native_replay.db'); p.add_argument('cmd',choices=['summary','transitions','cases','trace','claims']); p.add_argument('--sample'); p.add_argument('--limit',type=int,default=10); a=p.parse_args()
con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; cur=con.cursor()
if a.cmd=='summary':
    [print(f"{r['key']}: {r['value']}") for r in cur.execute('select * from pass13_run_manifest order by key')]
elif a.cmd=='transitions':
    [print(dict(r)) for r in cur.execute('select * from pass13_state_transition_summary order by scenario_id, transition_class')]
elif a.cmd=='cases':
    [print(dict(r)) for r in cur.execute('select sample_id,scenario_id,trajectory_trace_id,concise_interpretation from pass13_case_study_trace limit ?', (a.limit,))]
elif a.cmd=='trace':
    assert a.sample, '--sample required'
    [print(dict(r)) for r in cur.execute('select stage_order,scenario_id,stage_name,output_ref,p_status,r_status,xin_status,directness_class from pass13_native_replay_stage_output where sample_id=? order by scenario_id,stage_order',(a.sample,))]
elif a.cmd=='claims':
    [print(dict(r)) for r in cur.execute('select * from pass13_empirical_claim_boundary order by claim_id')]
