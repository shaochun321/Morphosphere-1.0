#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m362.db'); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor(); ok=True
print('v36.2 action downgrade audit')
queries=[
 ('continuous solver claim',"SELECT continuous_variational_solver_claimed FROM v362_run_manifest",0),
 ('physical action claim',"SELECT physical_action_claimed FROM v362_run_manifest",0),
 ('global solve claim',"SELECT global_action_solve_claimed FROM v362_run_manifest",0),
 ('delta Xin main definition rows',"SELECT COUNT(*) FROM v362_delta_xin_fallback_snapshot WHERE used_as_main_definition != 0",0),
 ('Xin direct-to-P/R rows',"SELECT COUNT(*) FROM v362_xin_var_closure_defect WHERE direct_to_pr_allowed != 0",0),
 ('promotion rows',"SELECT COUNT(*) FROM v362_action_comparison_report WHERE promotion_allowed != 0",0)]
for name,q,expected in queries:
 val=cur.execute(q).fetchone()[0]; print(f'{name}: {val}')
 if val!=expected: ok=False
print('meta proxies:',cur.execute('SELECT COUNT(*) FROM v362_meta_proxy_registry').fetchone()[0])
sys.exit(0 if ok else 1)
