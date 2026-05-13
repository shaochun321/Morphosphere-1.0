#!/usr/bin/env python3
import sqlite3, sys
p=sys.argv[1] if len(sys.argv)>1 else 'outputs/morphosphere_frozen_sandbox_v18_output_database.db'
con=sqlite3.connect(p)
checks=[]
def q(sql): return con.execute(sql).fetchone()[0]
def add(n,ok,obs,exp): checks.append((n,ok,obs,exp))
add('quick_check', q('PRAGMA quick_check')=='ok', q('PRAGMA quick_check'), 'ok')
add('profiles', q('select count(*) from sandbox_profile_registry_v18')==2, q('select count(*) from sandbox_profile_registry_v18'), '2')
add('scenarios', q('select count(*) from sandbox_replay_scenario_v18')>=10, q('select count(*) from sandbox_replay_scenario_v18'), '>=10')
add('metrics', q('select count(*) from sandbox_profile_metric_v18')==20, q('select count(*) from sandbox_profile_metric_v18'), '20')
add('not_auto_applied', q('select auto_applied from sandbox_decision_v18')==0, q('select auto_applied from sandbox_decision_v18'), '0')
add('not_promoted', q('select candidate_promoted from sandbox_decision_v18')==0, q('select candidate_promoted from sandbox_decision_v18'), '0')
add('manual_review', q('select manual_review_required from sandbox_decision_v18')==1, q('select manual_review_required from sandbox_decision_v18'), '1')
passed=sum(1 for _,ok,_,_ in checks if ok)
for n,ok,obs,exp in checks: print(f"{n}: {'PASS' if ok else 'FAIL'} observed={obs} expected={exp}")
print(f"frozen_sandbox_v1.8 acceptance: {passed} / {len(checks)} PASS")
sys.exit(0 if passed==len(checks) else 1)
