#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m365.db'); args=p.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor()
qc=cur.execute('pragma quick_check').fetchone()[0]
print('SQLite quick_check:', qc)
checks=cur.execute('select check_id,status,details,blocking from v365_acceptance_report order by check_id').fetchall()
fail=[r for r in checks if r[1] != 'PASS' and r[3]]
for cid,status,details,blocking in checks:
    print(f'{status:4} {cid}: {details}' + (' [blocking]' if blocking else ''))
for t in ['v365_upper_recursion_semantic_null_contract','v365_xin_minimal_carrier_state','v365_external_xin_definition_ref','v365_external_real_input_envelope_binding','v365_external_semantic_readout_result','v365_semantic_contamination_audit','v365_readout_backwrite_block_event','v365_acceptance_report']:
    print(f'{t}:', cur.execute(f'select count(*) from {t}').fetchone()[0])
if qc != 'ok' or fail:
    sys.exit(1)
print('V365_SEMANTIC_STRIPPING_EXTERNAL_READOUT_ACCEPTANCE: PASS')
