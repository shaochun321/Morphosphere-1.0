#!/usr/bin/env bash
set -euo pipefail
DB="outputs/v366/m366_build_pass6.db"
python3 - <<'PYCODE'
import sqlite3
p='outputs/v366/m366_build_pass6.db'
con=sqlite3.connect(p); cur=con.cursor()
checks={}
for t in ['pass6_lineage_trace_index','pass6_backtrace_sample','pass6_module_health_score','pass6_collaboration_edge_index']:
    checks[t]=cur.execute(f'select count(*) from {t}').fetchone()[0]
print('[PASS6]', checks)
assert checks['pass6_lineage_trace_index'] >= 500
assert checks['pass6_backtrace_sample'] >= 12
assert checks['pass6_module_health_score'] >= 7
assert checks['pass6_collaboration_edge_index'] >= 10
bad=cur.execute("select count(*) from pass6_acceptance_report where status!='PASS'").fetchone()[0]
assert bad == 0
print('[PASS6] acceptance PASS')
con.close()
PYCODE
python3 scripts/query_v366_lineage.py --db "$DB" status >/tmp/pass6_status.json
python3 scripts/query_v366_lineage.py --db "$DB" samples --limit 2 >/tmp/pass6_samples.json
printf '[PASS6] query CLI PASS
'
