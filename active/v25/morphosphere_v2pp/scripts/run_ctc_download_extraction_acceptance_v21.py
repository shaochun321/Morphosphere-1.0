#!/usr/bin/env python3
import sqlite3, sys
p=sys.argv[1]
con=sqlite3.connect(p); cur=con.cursor()
checks=[]
try:
    checks.append(('quick_check', cur.execute('PRAGMA quick_check').fetchone()[0]=='ok'))
except Exception:
    checks.append(('quick_check', False))
for table in ['ctc_dataset_download_plan_v21','ctc_centroid_schema_v21','ctc_extracted_centroid_sample_v21','ctc_centroid_quality_report_v21','ctc_realdata_readiness_gate_v21','ctc_v21_acceptance_report']:
    try:
        n=cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        checks.append((table,n>0))
    except Exception:
        checks.append((table,False))
fail=[n for n,ok in checks if not ok]
print('ctc_download_extraction_v2.1 acceptance: %d / %d PASS' % (len(checks)-len(fail), len(checks)))
for n,ok in checks: print(('PASS' if ok else 'FAIL'), n)
con.close()
sys.exit(1 if fail else 0)
