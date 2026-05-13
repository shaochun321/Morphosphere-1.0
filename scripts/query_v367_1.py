#!/usr/bin/env python3
import argparse, sqlite3

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='m367_1_native_anchor_hardening.db')
    ap.add_argument('cmd', choices=['summary','acceptance','zones','sample','legacy'])
    ap.add_argument('--limit', type=int, default=5)
    a=ap.parse_args()
    con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
    if a.cmd=='summary':
        for t in ['v367_native_anchor_fact','v367_anchor_validation_result','v367_dark_grid_zone_index']:
            print(t, con.execute(f'select count(*) n from {t}').fetchone()['n'])
    elif a.cmd=='acceptance':
        for r in con.execute('select check_name,status,observed_value,required_value,note from v367_acceptance_report order by check_id'):
            print(dict(r))
    elif a.cmd=='zones':
        for r in con.execute('select * from v367_dark_grid_zone_index order by anchor_count desc limit ?', (a.limit,)):
            print(dict(r))
    elif a.cmd=='sample':
        for r in con.execute('select anchor_fact_id,process_window_id,hypernode_id,information_point_ref,trajectory_window_ref,ledger_window_ref,dark_grid_zone_id from v367_native_anchor_fact limit ?', (a.limit,)):
            print(dict(r))
    elif a.cmd=='legacy':
        for r in con.execute('select * from v367_legacy_directness_comparison'):
            print(dict(r))
    con.close()
if __name__=='__main__': main()
