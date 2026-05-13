#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m362.db'); p.add_argument('--limit',type=int,default=5); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
q = "SELECT p.path_id,p.path_role,s.functional_id,s.total_action_proxy,x.xin_var_total,r.recommendation FROM v362_candidate_path_inventory p JOIN v362_discrete_action_score s USING(path_id) JOIN v362_xin_var_closure_defect x USING(path_id) JOIN v362_action_comparison_report r USING(path_id) ORDER BY s.total_action_proxy ASC LIMIT ?"
rows=cur.execute(q,(a.limit,)).fetchall()
print('lowest action proxy paths')
for row in rows: print(row)
