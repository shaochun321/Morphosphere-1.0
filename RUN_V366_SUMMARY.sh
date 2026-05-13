#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import sqlite3
root=Path('.').resolve()

def q(db, sql):
    con=sqlite3.connect(str(db)); con.row_factory=sqlite3.Row
    rows=[dict(r) for r in con.execute(sql).fetchall()]
    con.close(); return rows

m365=root/'outputs/v366/m365_full_chain_materialized.db'
m366=root/'outputs/v366/m366_process_window.db'
imp=root/'outputs/v366/m366_improvement_pass1.db'
imp2=root/'outputs/v366/m366_improvement_pass2.db'
merged=root/'outputs/v366/m366_process_window_pass2.db'
if not m365.exists(): m365=root/'active/v366_process_window/db/m365_full_chain_materialized.db'
if not m366.exists(): m366=root/'active/v366_process_window/db/m366_process_window.db'
if not imp.exists(): imp=root/'active/v366_process_window/db/m366_improvement_pass1.db'
if not imp2.exists(): imp2=root/'active/v366_process_window/db/m366_improvement_pass2.db'
if not merged.exists(): merged=root/'active/v366_process_window/db/m366_process_window_pass2.db'

print('\n## Full-chain object counts')
for r in q(m365, 'select layer_name, object_count from cross_layer_object_count order by layer_name'):
    print(f"{r['layer_name']}: {r['object_count']}")

print('\n## v36.6 process windows')
for r in q(m366, 'select window_kind, count(*) as n from v366_process_window_registry group by window_kind order by n desc'):
    print(f"{r['window_kind']}: {r['n']}")

print('\n## v36.6 process-window summary')
for r in q(m366, 'select metric, value from v366_process_window_summary order by metric'):
    print(f"{r['metric']}: {r['value']}")

print('\n## v36.6 pass1 quality classes')
for r in q(imp, 'select quality_class, count(*) as n from process_window_quality_score group by quality_class order by n desc'):
    print(f"{r['quality_class']}: {r['n']}")

print('\n## Stage2 summary')
for r in q(imp, 'select metric, value from stage2_summary order by metric'):
    print(f"{r['metric']}: {r['value']}")

print('\n## v36.6 improvement pass2')
if imp2.exists():
    for r in q(imp2, 'select object_name, object_count from pass2_object_counts order by object_name'):
        print(f"{r['object_name']}: {r['object_count']}")
    print('\n## v36.6 pass2 acceptance')
    for r in q(imp2, 'select check_name, status, observed_value from pass2_acceptance_report order by check_id'):
        print(f"{r['check_name']}: {r['status']} ({r['observed_value']})")
else:
    print('pass2 DB not found')

print('\n## v36.6 merged pass2 DB')
if merged.exists():
    con=sqlite3.connect(str(merged)); cur=con.cursor()
    print('integrity:', cur.execute('PRAGMA integrity_check').fetchone()[0])
    print('tables:', cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0])
    con.close()
else:
    print('merged DB not found')
PY

echo ""
echo "## v36.6 improvement pass3"
python3 - <<'PY'
import sqlite3
from pathlib import Path
p=Path('outputs/v366/m366_process_window_pass3.db')
if not p.exists():
    print('m366_process_window_pass3.db: missing')
else:
    con=sqlite3.connect(p); cur=con.cursor()
    print('integrity:', cur.execute('pragma integrity_check').fetchone()[0])
    for table in ['pass3_object_counts','process_window_materialization_confidence_pass3','stage2_bypass_and_route_legitimacy_pass3','pass3_acceptance_report']:
        print(f'{table}:', cur.execute(f'select count(*) from {table}').fetchone()[0])
    print('materialization_confidence:')
    for k,c in cur.execute('select materialization_confidence_class,count(*) from process_window_materialization_confidence_pass3 group by materialization_confidence_class order by 1'):
        print(f'  {k}: {c}')
    print('stage2_route_status:')
    for k,c in cur.execute('select stage2_route_status,count(*) from stage2_bypass_and_route_legitimacy_pass3 group by stage2_route_status order by 1'):
        print(f'  {k}: {c}')
    con.close()
PY
