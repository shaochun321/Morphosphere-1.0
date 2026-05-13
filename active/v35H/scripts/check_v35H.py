#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db',required=True); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
need={'v35h_hypernode_registry':747,'v35h_hyperedge_proposal':120,'v35h_hyperedge_incidence':855,'v35h_hyperedge_ledger_weight':120,'v35h_hyperedge_gc_report':12,'v35h_hyperedge_appeal_registry':10,'v35h_runtime_manifest':3}
for t,n in need.items():
    c=cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    if c!=n: raise SystemExit(f'FAIL {t}: {c}!={n}')
acc=cur.execute("SELECT COUNT(*) FROM v35h_acceptance_report WHERE status='PASS'").fetchone()[0]
if acc<12: raise SystemExit('FAIL acceptance')
print('PASS v35H bridge overlay')
