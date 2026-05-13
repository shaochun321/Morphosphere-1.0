#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path
root = Path(__file__).resolve().parents[2]
db = root / 'outputs' / 'morphosphere_shadow_reconstruction_v26_output_database.db'
con=sqlite3.connect(db); cur=con.cursor()
checks=[]
checks.append(('sqlite_quick_check', cur.execute('PRAGMA quick_check').fetchone()[0]=='ok'))
expected={
 'shadow_cell_identity_v26':86,
 'shadow_spacetime_cell_v26':4575,
 'shadow_cell_sphere_mapping_v26':4575,
 'shadow_cell_motion_state_v26':532,
 'shadow_pr_xi_comparison_v26':532,
 'shadow_decision_evidence_bridge_v26':532,
}
for t,n in expected.items():
    checks.append((t, cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0] == n))
checks.append(('acceptance_passes', cur.execute("SELECT count(*) FROM shadow_reconstruction_acceptance_report_v26 WHERE status!='PASS'").fetchone()[0] == 0))
failed=[k for k,ok in checks if not ok]
if failed:
    print('V26_SHADOW_ACCEPTANCE: FAIL')
    for k in failed: print('-', k)
    sys.exit(1)
print('V26_SHADOW_ACCEPTANCE: PASS')
for t in expected:
    print(f'{t}:', cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0])
