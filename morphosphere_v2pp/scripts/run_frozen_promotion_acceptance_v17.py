#!/usr/bin/env python3
import sqlite3, sys, json
from pathlib import Path

def main():
    db = Path(sys.argv[1]) if len(sys.argv)>1 else Path('outputs/morphosphere_frozen_promotion_v17_output_database.db')
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    print('quick_check:', cur.execute('PRAGMA quick_check').fetchone()[0])
    print('decision:', cur.execute('SELECT final_decision FROM promotion_decision_v17 LIMIT 1').fetchone()[0])
    rows=cur.execute('SELECT check_id, passed, details FROM frozen_promotion_acceptance_report_v17 ORDER BY check_id').fetchall()
    passed=sum(r[1] for r in rows)
    print(f'frozen_promotion_v1.7 acceptance: {passed}/{len(rows)} PASS')
    for cid,p,details in rows:
        print(('PASS' if p else 'FAIL'), cid, '-', details)
    sys.exit(0 if passed==len(rows) else 1)
if __name__=='__main__': main()
