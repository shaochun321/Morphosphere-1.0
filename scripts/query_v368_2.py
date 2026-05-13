#!/usr/bin/env python3
import sqlite3, argparse, json
p=argparse.ArgumentParser()
p.add_argument('--db', default='m368_2_mainline_trace_expansion_state_audit.db')
p.add_argument('cmd', choices=['summary','roles','trace','masking','readout','acceptance'])
p.add_argument('--id')
p.add_argument('--limit', type=int, default=10)
a=p.parse_args()
con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
if a.cmd=='summary':
    for r in con.execute('select * from v3682_run_manifest'): print(dict(r))
    print(dict(con.execute("select (select count(*) from v3682_mainline_trace_expanded) traces, (select count(*) from v3682_state_transition_reason_audit) reasons, (select count(*) from v3682_attention_coupling_audit) attention").fetchone()))
elif a.cmd=='roles':
    for r in con.execute('select role_proxy, count(*) n, avg(p_value) p, avg(r_value) r, avg(xin_value) xin from v3682_mainline_trace_expanded group by role_proxy order by n desc'): print(dict(r))
elif a.cmd=='trace':
    if a.id:
        q='select * from v3682_mainline_trace_expanded where trace_id=? or trajectory_trace_id=?'; params=(a.id,a.id)
    else:
        q='select * from v3682_mainline_trace_expanded limit ?'; params=(a.limit,)
    for r in con.execute(q,params): print(json.dumps(dict(r),ensure_ascii=False,indent=2))
elif a.cmd=='masking':
    for r in con.execute('select * from v3682_masking_effect_audit order by window_count desc limit ?', (a.limit,)): print(dict(r))
elif a.cmd=='readout':
    for r in con.execute('select * from v3682_external_readout_boundary_audit limit ?', (a.limit,)): print(dict(r))
elif a.cmd=='acceptance':
    for r in con.execute('select * from v3682_functional_acceptance_report'): print(dict(r))
