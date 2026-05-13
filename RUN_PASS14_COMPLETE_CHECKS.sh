#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import sqlite3, pathlib, json
root = pathlib.Path('.')
checks = [
    ('outputs/m25.db', None),
    ('outputs/m34.db', None),
    ('outputs/m365_full_rebase.db', None),
    ('outputs/v366/m365_full_chain_materialized.db', None),
    ('outputs/v366/m366_process_window_pass3.db', 'v366_process_window_registry'),
    ('outputs/v366/m366_implementation_coverage_audit.db', None),
    ('outputs/v366/m366_build_pass12_execution.db', 'pass12_native_skeleton_trace'),
    ('outputs/v366/m366_build_pass13_native_replay.db', 'pass13_replay_sample_set'),
]
summary = []
for rel, table in checks:
    p = root / rel
    if not p.exists():
        raise SystemExit(f'MISSING: {rel}')
    con = sqlite3.connect(str(p))
    ok = con.execute('PRAGMA integrity_check').fetchone()[0]
    if ok != 'ok':
        raise SystemExit(f'INTEGRITY_FAIL: {rel}: {ok}')
    row_count = None
    if table:
        row_count = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        if row_count <= 0:
            raise SystemExit(f'EMPTY_REQUIRED_TABLE: {rel}:{table}')
    con.close()
    summary.append({'db': rel, 'integrity': ok, 'required_table': table, 'row_count': row_count})
print(json.dumps({'pass14_complete_checks':'PASS','checks':summary}, indent=2))
PY
