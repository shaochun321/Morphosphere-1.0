#!/usr/bin/env python3
import argparse, sqlite3, sys
REQ=['v31_run_manifest','v31_policy_belief_state','v31_active_loop_cycle','v31_action_observation_trace','v31_policy_update','v31_macro_policy_binding','v31_guardrail_audit','v31_acceptance_report']
def main():
 p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m31.db'); a=p.parse_args(); con=sqlite3.connect(a.db); cur=con.cursor(); q=cur.execute('pragma quick_check').fetchone()[0]; print('SQLite quick_check:',q); bad=[]
 for t in REQ:
  c=cur.execute(f'select count(*) from {t}').fetchone()[0]; print(f'{t}: {c}');
  if c<1: bad.append(t)
 ok=cur.execute("select count(*) from v31_acceptance_report where status='PASS'").fetchone()[0]; total=cur.execute('select count(*) from v31_acceptance_report').fetchone()[0]; print(f'v31_acceptance_report: {ok}/{total} PASS')
 if q!='ok' or bad or ok!=total: sys.exit(1)
 print('V31_ACTIVE_INFERENCE_LOOP_ACCEPTANCE: PASS')
if __name__=='__main__': main()
