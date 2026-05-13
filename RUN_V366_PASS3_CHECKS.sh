#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import sqlite3, json, pathlib
root = pathlib.Path('.')
db = root/'outputs/v366/m366_process_window_pass3.db'
con = sqlite3.connect(db)
cur = con.cursor()
print('[PASS3] integrity:', cur.execute('pragma integrity_check').fetchone()[0])
for table in [
    'v366_process_window_registry',
    'stage2_bypass_and_route_legitimacy_pass3',
    'process_window_materialization_confidence_pass3',
    'hypernode_fk_direct_coverage_pass3',
    'pass3_acceptance_report'
]:
    print(f'[PASS3] {table}:', cur.execute(f'select count(*) from {table}').fetchone()[0])
print('[PASS3] materialization confidence:')
for row in cur.execute("select materialization_confidence_class, count(*) from process_window_materialization_confidence_pass3 group by materialization_confidence_class order by 1"):
    print(' ', row[0], row[1])
print('[PASS3] route status:')
for row in cur.execute("select stage2_route_status, count(*) from stage2_bypass_and_route_legitimacy_pass3 group by stage2_route_status order by 1"):
    print(' ', row[0], row[1])
fail = list(cur.execute("select check_id, check_name, status, observed from pass3_acceptance_report where status not in ('PASS','WARN')"))
if fail:
    raise SystemExit('Pass3 acceptance failure: '+json.dumps(fail))
print('[PASS3] acceptance: PASS')
con.close()
PY
