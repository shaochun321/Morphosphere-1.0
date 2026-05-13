#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
DB="outputs/v366/m366_improvement_pass2.db"
MERGED="outputs/v366/m366_process_window_pass2.db"
if [ ! -f "$DB" ]; then DB="active/v366_process_window/db/m366_improvement_pass2.db"; fi
if [ ! -f "$MERGED" ]; then MERGED="active/v366_process_window/db/m366_process_window_pass2.db"; fi
python3 - <<PY
import sqlite3
from pathlib import Path
for label,path in [('pass2',Path('$DB')),('merged',Path('$MERGED'))]:
    con=sqlite3.connect(path); cur=con.cursor()
    print(f"[{label}] {path}")
    print(' integrity:', cur.execute('PRAGMA integrity_check').fetchone()[0])
    if label=='pass2':
        for name,note in cur.execute('SELECT object_name, object_count FROM pass2_object_counts ORDER BY object_name'):
            print(f" {name}: {note}")
        bad=cur.execute("SELECT COUNT(*) FROM pass2_acceptance_report WHERE status='FAIL'").fetchone()[0]
        if bad:
            raise SystemExit(f'FAIL: {bad} pass2 acceptance checks failed')
    con.close()
PY
