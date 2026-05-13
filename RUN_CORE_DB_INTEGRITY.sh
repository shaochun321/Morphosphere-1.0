#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
from pathlib import Path
import sqlite3, os
root=Path('.').resolve()
paths=[
 root/'outputs/m365_full_rebase.db',
 root/'outputs/m365.db',
 root/'outputs/m35H.db',
 root/'outputs/v366/m365_full_chain_materialized.db',
 root/'outputs/v366/m366_improvement_pass3.db',
 root/'outputs/v366/m366_process_window_pass3.db',
]
if os.environ.get('RUN_FULL_DB_INTEGRITY') == '1':
    paths=sorted(list((root/'outputs').glob('*.db')) + list((root/'outputs'/'v366').glob('*.db')))
failed=[]
for p in paths:
    if not p.exists():
        print(f'{p}: MISSING'); failed.append((str(p),'MISSING')); continue
    con=sqlite3.connect(str(p)); res=con.execute('pragma integrity_check').fetchone()[0]; con.close()
    print(f'{p}: {res}')
    if res!='ok': failed.append((str(p),res))
if failed: raise SystemExit(failed)
PY
