#!/usr/bin/env python3
import argparse, sqlite3, json
from pathlib import Path

def rows(db,q,args=()):
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    out=[dict(r) for r in con.execute(q,args).fetchall()]
    con.close(); return out

def print_table(rs):
    if not rs:
        print('(no rows)'); return
    cols=list(rs[0].keys())
    print('\t'.join(cols))
    for r in rs:
        print('\t'.join(str(r.get(c,'')) for c in cols))

p=argparse.ArgumentParser()
p.add_argument('--db', default='outputs/v366/m366_build_pass11_parallel.db')
p.add_argument('cmd', choices=['lanes','skeleton','stress','empirical','coverage','externals','acceptance','summary'])
p.add_argument('--limit', type=int, default=20)
a=p.parse_args()
db=a.db
if a.cmd=='lanes':
    print_table(rows(db,'select lane_id,lane_name,placement,status,boundary_note from pass11_parallel_lane_manifest order by lane_id'))
elif a.cmd=='skeleton':
    print_table(rows(db,'select step_order,step_name,current_materialized_count,current_status,upgrade_needed from pass11_native_full_chain_skeleton order by step_order'))
elif a.cmd=='stress':
    print_table(rows(db,'select stress_case_id,perturbation_type,expected_observable,maturity,should_not_claim from pass11_stress_suite_plan order by stress_case_id limit ?', (a.limit,)))
elif a.cmd=='empirical':
    print_table(rows(db,'select finding_id,finding_type,metric,value,interpretation,limitation from pass11_upper_layer_empirical_v2 order by finding_id limit ?', (a.limit,)))
elif a.cmd=='coverage':
    print_table(rows(db,'select concept_id,concept_name,pass10_maturity,pass11_treatment,status_after_pass11 from pass11_coverage_delta order by concept_id limit ?', (a.limit,)))
elif a.cmd=='externals':
    print_table(rows(db,'select module_name,module_type,sync_mode,can_write_mainline,allowed_outputs,forbidden_outputs from pass11_external_module_parallel_boundary'))
elif a.cmd=='acceptance':
    print_table(rows(db,'select * from pass11_acceptance_report'))
elif a.cmd=='summary':
    print(json.dumps({
        'lanes': rows(db,'select count(*) as n from pass11_parallel_lane_manifest')[0]['n'],
        'skeleton_steps': rows(db,'select count(*) as n from pass11_native_full_chain_skeleton')[0]['n'],
        'stress_cases': rows(db,'select count(*) as n from pass11_stress_suite_plan')[0]['n'],
        'empirical_findings': rows(db,'select count(*) as n from pass11_upper_layer_empirical_v2')[0]['n'],
        'acceptance_pass': rows(db,"select count(*) as n from pass11_acceptance_report where status='PASS'")[0]['n']
    }, indent=2))
