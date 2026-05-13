#!/usr/bin/env python3
import argparse, sqlite3, sys

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='outputs/m32.db')
    args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor()
    qc=cur.execute('PRAGMA quick_check').fetchone()[0]
    if qc!='ok': print('FAIL quick_check',qc); sys.exit(1)
    rows=cur.execute("SELECT check_id,status,details FROM v32_acceptance_report ORDER BY check_id").fetchall()
    failed=[r for r in rows if r[1] != 'PASS']
    for r in rows: print(f'{r[0]} {r[1]} {r[2]}')
    if failed: sys.exit(2)
    print('V32_ACCEPTANCE: PASS')
if __name__=='__main__': main()
