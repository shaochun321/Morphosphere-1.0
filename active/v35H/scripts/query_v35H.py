#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',required=True); p.add_argument('--limit',type=int,default=5); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
for r in cur.execute('SELECT h.hyperedge_id, h.ledger_decision, h.final_weight, COUNT(i.node_id) FROM v35h_hyperedge_ledger_weight h JOIN v35h_hyperedge_incidence i USING(hyperedge_id) GROUP BY h.hyperedge_id ORDER BY h.final_weight DESC LIMIT ?', (a.limit,)):
    print(r)
