#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db', default='outputs/m28.db'); args=p.parse_args()
con=sqlite3.connect(args.db)
qc=con.execute('pragma quick_check(1)').fetchone()[0]
print('SQLite quick_check:', qc)
checks=con.execute('select check_id,status,details from v28_acceptance_report order by check_id').fetchall()
for cid,status,details in checks: print(f'{status:4s} {cid}: {details}')
if qc!='ok' or any(s!='PASS' for _,s,_ in checks): sys.exit(1)
for t in ['v28_evidence_edge','v28_shadow_edge','v28_shadow_evidence_alignment','v28_divergence_decomposition','v28_confirmed_p_structure','v28_shadow_overreach_penalty','v28_evidence_surprise_xi','v28_emergence_alert_candidate']:
    print(f'{t}:', con.execute(f'select count(*) from {t}').fetchone()[0])
print('V28_ACCEPTANCE: PASS')
