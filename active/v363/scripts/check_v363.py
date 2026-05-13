#!/usr/bin/env python3
import argparse, sqlite3, sys
REQUIRED = {
 'v363_p_relative_stasis_profile': 1,
 'v363_spacetime_block_registry': 1,
 'v363_r_spacetime_band_candidate': 1,
 'v363_band_segment_link': 1,
 'v363_xin_noncontinuity_ledger': 1,
 'v363_pseudo_continuity_audit': 1,
 'v363_downgrade_contract': 1,
 'v363_acceptance_report': 12,
}
parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
args = parser.parse_args()
con = sqlite3.connect(args.db)
cur = con.cursor()
if cur.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
    print('FAIL sqlite integrity')
    sys.exit(1)
for table, minimum in REQUIRED.items():
    n = cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {n}')
    if n < minimum:
        print(f'FAIL {table} expected at least {minimum}')
        sys.exit(1)
ident = dict(cur.execute('SELECT key,value FROM v363_package_identity').fetchall())
assert ident.get('artifact_type') == 'ENGINEERED_BRIDGE_OVERLAY'
assert ident.get('includes_full_base') == 'false'
assert ident.get('not_a_full_lineage') == 'true'
failures = cur.execute("SELECT COUNT(*) FROM v363_acceptance_report WHERE status!='PASS'").fetchone()[0]
if failures:
    print('FAIL acceptance failures')
    sys.exit(1)
print('PASS v36.3 bridge overlay acceptance')
