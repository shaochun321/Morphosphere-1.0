#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m34.db'); args=p.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor()
qc=cur.execute('pragma quick_check').fetchone()[0]
checks=cur.execute('select check_id,status,details from v34_acceptance_report order by check_id').fetchall()
print('SQLite quick_check:',qc)
fail=[r for r in checks if r[1] != 'PASS']
for cid,status,details in checks: print(f'{status:4} {cid}: {details}')
for t in ['v34_proxy_registry','v34_proxy_dependency_edge','v34_proxy_propagation_path','v34_external_entropy_event','v34_proxy_entropy_binding','v34_noether_balance_audit','v34_acceptance_report']:
    print(f'{t}:',cur.execute(f'select count(*) from {t}').fetchone()[0])
if qc!='ok' or fail:
    sys.exit(1)
print('V34_PROXY_ENTROPY_ACCEPTANCE: PASS')
