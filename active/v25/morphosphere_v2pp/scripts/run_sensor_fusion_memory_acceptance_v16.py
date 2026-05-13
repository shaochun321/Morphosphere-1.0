#!/usr/bin/env python3
import sqlite3, sys

def main():
    db=sys.argv[1] if len(sys.argv)>1 else 'outputs/morphosphere_sensor_fusion_memory_v16_output_database.db'
    con=sqlite3.connect(db)
    cur=con.cursor()
    rows=cur.execute('select check_id, passed, details from sensor_fusion_memory_acceptance_report_v16 order by check_id').fetchall()
    passed=sum(1 for _,p,_ in rows if p)
    for cid,p,details in rows:
        print(f'{cid}: {"PASS" if p else "FAIL"} - {details}')
    print(f'sensor_fusion_memory_v1.6 acceptance: {passed} / {len(rows)} PASS')
    con.close()
    if passed != len(rows): sys.exit(1)
if __name__=='__main__': main()
