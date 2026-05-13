#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import sqlite3

def q(db, sql):
    con=sqlite3.connect(str(db)); con.row_factory=sqlite3.Row
    rows=[dict(r) for r in con.execute(sql).fetchall()]
    con.close(); return rows

print('## v36.5 full-chain materialized counts')
m365=Path('outputs/v366/m365_full_chain_materialized.db')
for r in q(m365, 'select layer_name, object_count from cross_layer_object_count order by layer_name'):
    print(f"{r['layer_name']}: {r['object_count']}")

print('\n## v36.6 pass3 process windows')
p=Path('outputs/v366/m366_process_window_pass3.db')
con=sqlite3.connect(p); cur=con.cursor()
print('integrity:', cur.execute('pragma integrity_check').fetchone()[0])
for table in ['v366_process_window_registry','v366_process_window_member','process_window_materialization_confidence_pass3','stage2_bypass_and_route_legitimacy_pass3','hypernode_fk_direct_coverage_pass3','pass3_acceptance_report']:
    print(f'{table}:', cur.execute(f'select count(*) from {table}').fetchone()[0])
print('materialization_confidence:')
for k,c in cur.execute('select materialization_confidence_class,count(*) from process_window_materialization_confidence_pass3 group by materialization_confidence_class order by 1'):
    print(f'  {k}: {c}')
print('stage2_route_status:')
for k,c in cur.execute('select stage2_route_status,count(*) from stage2_bypass_and_route_legitimacy_pass3 group by stage2_route_status order by 1'):
    print(f'  {k}: {c}')
con.close()
PY
