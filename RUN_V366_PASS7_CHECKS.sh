#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass7.db"
python3 - <<'PYCODE'
import sqlite3
p='outputs/v366/m366_build_pass7.db'
con=sqlite3.connect(p); cur=con.cursor()
checks={}
for t in ['pass7_native_write_contract','pass7_upstream_writer_upgrade_plan','pass7_directness_debt_index','pass7_native_write_candidate_index','pass7_module_readiness_matrix']:
    checks[t]=cur.execute(f'select count(*) from {t}').fetchone()[0]
print('[PASS7]', checks)
assert checks['pass7_native_write_contract'] >= 6
assert checks['pass7_upstream_writer_upgrade_plan'] >= 5
assert checks['pass7_directness_debt_index'] >= 5
assert checks['pass7_native_write_candidate_index'] >= 500
bad=cur.execute("select count(*) from pass7_acceptance_report where status='FAIL'").fetchone()[0]
assert bad == 0
print('[PASS7] acceptance PASS')
con.close()
PYCODE
python3 scripts/query_v366_lineage_pass7.py --db "$DB" status >/tmp/pass7_status.json
python3 scripts/query_v366_lineage_pass7.py --db "$DB" debt >/tmp/pass7_debt.json
printf '[PASS7] query CLI PASS\n'
