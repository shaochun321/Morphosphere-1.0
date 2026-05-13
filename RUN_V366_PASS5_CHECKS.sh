#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
import sqlite3
from pathlib import Path
p=Path('outputs/v366/m366_build_pass5.db')
if not p.exists(): p=Path('active/v366_process_window/db/m366_build_pass5.db')
con=sqlite3.connect(p); cur=con.cursor()
assert cur.execute('pragma integrity_check').fetchone()[0]=='ok'
for table,min_count in {'pass5_build_manifest':1,'pass5_deployment_mode_contract':2,'pass5_module_operation_status':10,'pass5_module_collaboration_matrix':10,'pass5_acceptance_report':7}.items():
    n=cur.execute(f'select count(*) from {table}').fetchone()[0]
    if n < min_count: raise SystemExit(f'{table}: {n} < {min_count}')
fail=cur.execute("select check_name,status from pass5_acceptance_report where status='FAIL'").fetchall()
if fail: raise SystemExit('pass5 failures: '+repr(fail))
print('[pass5] integrity: ok')
for row in cur.execute('select check_name,status,observed_value from pass5_acceptance_report order by check_id'):
    print('[pass5]', row[0]+':', row[1], '('+str(row[2])+')')
con.close()
PY
