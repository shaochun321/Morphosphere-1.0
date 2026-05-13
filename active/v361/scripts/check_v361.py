#!/usr/bin/env python3
import argparse, sqlite3, sys
REQ={'v361_action_functional_registry':4,'v361_candidate_path_inventory':120,'v361_external_ledger_lagrangian_proxy':120,'v361_variational_metric_state':120,'v361_stationarity_defect':120,'v361_xin_variational_defect':120,'v361_delta_xin_fallback_snapshot':120,'v361_action_scoring_report':120,'v361_downgrade_contract':8,'v361_acceptance_report':12}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m361.db'); a=p.parse_args()
 con=sqlite3.connect(a.db); cur=con.cursor(); ok=True
 print('v36.1 variational external ledger bridge check')
 for table, minimum in REQ.items():
  n=cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]; print(f'{table}: {n}')
  if n < minimum: ok=False
 q=cur.execute('PRAGMA quick_check').fetchone()[0]; print('quick_check:',q)
 if q!='ok': ok=False
 vals=cur.execute('SELECT includes_full_base,not_a_full_lineage,continuous_variational_solver_claimed,semantic_label_in_mainline FROM v361_run_manifest').fetchone()
 if vals!=(0,1,0,0): print('boundary tuple failed:',vals); ok=False
 bad=cur.execute('SELECT COUNT(*) FROM v361_xin_variational_defect WHERE direct_to_pr_allowed != 0').fetchone()[0]
 if bad: print('direct-to-P/R violations:',bad); ok=False
 passes=cur.execute("SELECT COUNT(*) FROM v361_acceptance_report WHERE status='PASS'").fetchone()[0]
 total=cur.execute('SELECT COUNT(*) FROM v361_acceptance_report').fetchone()[0]
 print(f'acceptance: {passes}/{total} PASS')
 if passes != total: ok=False
 sys.exit(0 if ok else 1)
if __name__=='__main__': main()
