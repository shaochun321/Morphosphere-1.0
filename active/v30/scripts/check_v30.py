#!/usr/bin/env python3
import sqlite3, argparse, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='outputs/m30.db')
    args=ap.parse_args()
    db=Path(args.db)
    con=sqlite3.connect(db); cur=con.cursor()
    print('SQLite quick_check:', cur.execute('pragma quick_check').fetchone()[0])
    for t in ['v30_confirmed_p_cluster','v30_effective_information_probe','v30_macro_node_candidate','v30_hierarchical_edge','v30_cross_level_attention_request','v30_macro_node_lineage']:
        print(f'{t}:', cur.execute(f'select count(*) from {t}').fetchone()[0])
    rows=cur.execute('select check_id,status,details from v30_acceptance_report order by check_id').fetchall()
    fails=[r for r in rows if r[1] != 'PASS']
    for r in rows: print(f'{r[0]}: {r[1]} - {r[2]}')
    if fails:
        sys.exit(1)
    print('V30_ACCEPTANCE: PASS')
if __name__=='__main__': main()
