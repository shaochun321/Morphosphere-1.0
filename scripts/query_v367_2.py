#!/usr/bin/env python3
import sqlite3, argparse
p=argparse.ArgumentParser()
p.add_argument('--db', default='outputs/v367/m367_2_safe_stress_guard_config.db')
p.add_argument('cmd', choices=['summary','rules','gates'])
args=p.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
if args.cmd=='summary':
    for r in cur.execute('select * from v3672_safe_stress_summary order by metric'):
        print(f"{r['metric']}: {r['value']}  # {r['note']}")
elif args.cmd=='rules':
    for r in cur.execute('select injection_location,intensity_label,masking_condition,guard_action,rule_reason from v3672_safe_stress_envelope_rule order by injection_location,intensity_label,masking_condition'):
        print(f"{r['injection_location']} | {r['intensity_label']} | {r['masking_condition']} -> {r['guard_action']} :: {r['rule_reason']}")
elif args.cmd=='gates':
    for r in cur.execute('select gate_name,gate_status,observed_value,required_value from v3672_regression_gate order by gate_id'):
        print(f"{r['gate_status']}: {r['gate_name']} ({r['observed_value']} / {r['required_value']})")
