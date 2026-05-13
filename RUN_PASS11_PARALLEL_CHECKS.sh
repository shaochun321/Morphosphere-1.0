#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass11_parallel.db"
python3 - <<'PY'
import sqlite3, sys, os
DB='outputs/v366/m366_build_pass11_parallel.db'
if not os.path.exists(DB):
    print('[FAIL] missing', DB); sys.exit(1)
con=sqlite3.connect(DB); cur=con.cursor()
print('[CHECK] integrity:', cur.execute('PRAGMA integrity_check').fetchone()[0])
required=['pass11_parallel_lane_manifest','pass11_native_full_chain_skeleton','pass11_stress_suite_plan','pass11_upper_layer_empirical_v2','pass11_coverage_delta','pass11_acceptance_report']
for t in required:
    n=cur.execute(f'select count(*) from {t}').fetchone()[0]
    print(f'[CHECK] {t}: {n}')
    if n <= 0:
        print('[FAIL] empty table', t); sys.exit(2)
fail=cur.execute("select count(*) from pass11_acceptance_report where status != 'PASS'").fetchone()[0]
if fail:
    print('[FAIL] non-PASS acceptance rows', fail); sys.exit(3)
print('[PASS] Pass11 parallel checks complete')
con.close()
PY
