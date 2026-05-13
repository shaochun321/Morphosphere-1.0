#!/usr/bin/env bash
set -euo pipefail
python3 - <<'INNEREOF'
import sqlite3
p='outputs/v366/m366_build_pass12_execution.db'
con=sqlite3.connect(p)
print('integrity:', con.execute('PRAGMA integrity_check').fetchone()[0])
print('stress_rows:', con.execute('select count(*) from pass12_stress_projection_result').fetchone()[0])
print('skeleton_rows:', con.execute('select count(*) from pass12_native_skeleton_trace').fetchone()[0])
print('acceptance_failures:', con.execute("select count(*) from pass12_acceptance_report where status!='PASS'").fetchone()[0])
INNEREOF
