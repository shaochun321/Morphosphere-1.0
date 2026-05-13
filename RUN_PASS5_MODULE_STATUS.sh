#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
import sqlite3
from pathlib import Path
p=Path('outputs/v366/m366_build_pass5.db')
if not p.exists(): p=Path('active/v366_process_window/db/m366_build_pass5.db')
con=sqlite3.connect(p); con.row_factory=sqlite3.Row
print('## Pass5 module operation status')
for r in con.execute('select module_id,layer_name,operational_status,materialized_rows,confidence_class,route_legitimacy from pass5_module_operation_status order by module_id'):
    print(f"{r['module_id']} | {r['layer_name']} | {r['operational_status']} | rows={r['materialized_rows']} | confidence={r['confidence_class']} | route={r['route_legitimacy']}")
print('\n## Pass5 collaboration matrix')
for r in con.execute('select edge_id,upstream_module,downstream_module,collaboration_type,link_hardness,observed_count from pass5_module_collaboration_matrix order by edge_id'):
    print(f"{r['edge_id']} | {r['upstream_module']} -> {r['downstream_module']} | {r['collaboration_type']} | {r['link_hardness']} | count={r['observed_count']}")
con.close()
PY
