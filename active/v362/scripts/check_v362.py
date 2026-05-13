#!/usr/bin/env python3
import argparse, sqlite3, sys
REQ={'v362_action_functional_candidate_library':5,'v362_candidate_path_inventory':120,'v362_discrete_action_score':120,'v362_stationarity_defect_proxy':120,'v362_xin_var_closure_defect':120,'v362_delta_xin_fallback_snapshot':120,'v362_action_comparison_report':120,'v362_meta_proxy_registry':12,'v362_downgrade_contract':9,'v362_acceptance_report':12}
def main():
 p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m362.db'); a=p.parse_args()
 con=sqlite3.connect(a.db); cur=con.cursor(); ok=True
 print('v36.2 variational action revision bridge check')
 for table, minimum in REQ.items():
  n=cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]; print(f'{table}: {n}')
  if n < minimum: ok=False
 q=cur.execute('PRAGMA quick_check').fetchone()[0]; print('quick_check:',q)
 if q!='ok': ok=False
 vals=cur.execute('SELECT includes_full_base,not_a_full_lineage,continuous_variational_solver_claimed,physical_action_claimed,global_action_solve_claimed,semantic_label_in_mainline FROM v362_run_manifest').fetchone()
 if vals!=(0,1,0,0,0,0): print('boundary tuple failed:',vals); ok=False
 bad=cur.execute('SELECT COUNT(*) FROM v362_xin_var_closure_defect WHERE direct_to_pr_allowed != 0').fetchone()[0]
 if bad: print('direct-to-P/R violations:',bad); ok=False
 dx=cur.execute('SELECT COUNT(*) FROM v362_delta_xin_fallback_snapshot WHERE used_as_main_definition != 0').fetchone()[0]
 if dx: print('Delta-Xin main-definition violations:',dx); ok=False
 passes=cur.execute("SELECT COUNT(*) FROM v362_acceptance_report WHERE status='PASS'").fetchone()[0]
 total=cur.execute('SELECT COUNT(*) FROM v362_acceptance_report').fetchone()[0]
 print(f'acceptance: {passes}/{total} PASS')
 if passes != total: ok=False
 sys.exit(0 if ok else 1)
if __name__=='__main__': main()
