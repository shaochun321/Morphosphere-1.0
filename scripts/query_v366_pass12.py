#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser()
p.add_argument('--db', default='outputs/v366/m366_build_pass12_execution.db')
p.add_argument('cmd', choices=['summary','stress','samples','skeleton'])
p.add_argument('--limit', type=int, default=5)
a=p.parse_args()
con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
if a.cmd=='summary':
    for r in con.execute('SELECT key,value FROM pass12_run_manifest ORDER BY key'):
        print(f"{r['key']}: {r['value']}")
    print('stress_rows:', con.execute('SELECT COUNT(*) FROM pass12_stress_projection_result').fetchone()[0])
    print('skeleton_rows:', con.execute('SELECT COUNT(*) FROM pass12_native_skeleton_trace').fetchone()[0])
elif a.cmd=='stress':
    for r in con.execute('SELECT * FROM pass12_execution_result_matrix ORDER BY stress_id'):
        print(dict(r))
elif a.cmd=='samples':
    for r in con.execute('SELECT sample_id, trajectory_trace_id, trace_narrative FROM pass12_sample_full_trace LIMIT ?', (a.limit,)):
        print(json.dumps(dict(r), ensure_ascii=False))
elif a.cmd=='skeleton':
    for r in con.execute('SELECT trace_id, stage_order, stage_name, trajectory_trace_id, input_ref, output_ref FROM pass12_native_skeleton_trace LIMIT ?', (a.limit,)):
        print(json.dumps(dict(r), ensure_ascii=False))
