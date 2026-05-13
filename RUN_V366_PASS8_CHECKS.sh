#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass8.db"
python3 - <<'PY'
import sqlite3, os, sys, json
DB='outputs/v366/m366_build_pass8.db'
if not os.path.exists(DB):
    print('[FAIL] missing', DB); sys.exit(1)
con=sqlite3.connect(DB)
print('[CHECK] integrity:', con.execute('pragma integrity_check').fetchone()[0])
req=[
 ('blueprint core alignment rows', 'select count(*) from pass8_blueprint_core_alignment', 8),
 ('component placement rows', 'select count(*) from pass8_component_placement_contract', 10),
 ('external module boundary rows', 'select count(*) from pass8_external_module_boundary', 3),
 ('full chain layer rows', 'select count(*) from pass8_full_chain_run_layer_contract', 10),
 ('acceptance pass rows', "select count(*) from pass8_acceptance_report where status='PASS'", 7),
]
for name,sql,minv in req:
    v=con.execute(sql).fetchone()[0]
    print(f'[CHECK] {name}: {v}')
    if v < minv:
        print('[FAIL]', name, 'expected >=', minv); sys.exit(2)
# boundary checks
bad=con.execute("select count(*) from pass8_component_placement_contract where belongs_to_external_module=1 and can_write_mainline<>0").fetchone()[0]
print('[CHECK] external modules can_write_mainline bad count:', bad)
if bad:
    sys.exit(3)
print('[PASS] Pass8 boundary checks passed')
PY
