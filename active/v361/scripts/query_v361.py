#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m361.db'); p.add_argument('--limit',type=int,default=5); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
sql = "SELECT path_id,total_action_proxy,stationarity_defect_total,xin_var_mass,verdict,recommended_next FROM v361_action_scoring_report ORDER BY total_action_proxy ASC LIMIT ?"
for row in cur.execute(sql,(a.limit,)):
 print(row)
