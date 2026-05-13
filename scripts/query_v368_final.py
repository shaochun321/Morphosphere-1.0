#!/usr/bin/env python3
import sqlite3, argparse, json
parser=argparse.ArgumentParser()
parser.add_argument('--db', default='m368_mainline_consolidated_final.db')
parser.add_argument('cmd', choices=['status','counts','roles','transitions','debt','gates'])
args=parser.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
if args.cmd=='status':
    for r in cur.execute('select * from final_status_view'): print(dict(r))
elif args.cmd=='counts':
    for r in cur.execute('select * from final_mainline_counts_view'): print(dict(r))
elif args.cmd=='roles':
    for r in cur.execute('select * from final_role_distribution order by window_count desc'): print(dict(r))
elif args.cmd=='transitions':
    for r in cur.execute('select * from mainline_transition_summary order by edge_count desc'): print(dict(r))
elif args.cmd=='debt':
    for r in cur.execute('select * from final_debt_view'): print(dict(r))
elif args.cmd=='gates':
    for r in cur.execute('select * from final_acceptance_gate order by gate_id'): print(dict(r))
