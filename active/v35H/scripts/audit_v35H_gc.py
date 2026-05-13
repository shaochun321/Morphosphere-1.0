#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',required=True); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
print('gc_rows', cur.execute('SELECT COUNT(*) FROM v35h_hyperedge_gc_report').fetchone()[0])
print('appeal_rows', cur.execute('SELECT COUNT(*) FROM v35h_hyperedge_appeal_registry').fetchone()[0])
