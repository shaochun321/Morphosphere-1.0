#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
python3 - <<'PY'
import sqlite3
from pathlib import Path
root=Path('.')
base=['m25.db','m26.db','m27.db','m28.db','m29.db','m30.db','m31.db','m32.db','m33.db','m34.db']
missing=[b for b in base if not (root/'outputs'/b).exists()]
if missing:
    print('full data audit: base DBs missing; likely quick deploy mode')
    print('missing:', ', '.join(missing))
    raise SystemExit(0)
print('full data audit: base DBs present')
for b in base:
    p=root/'outputs'/b
    con=sqlite3.connect(p); cur=con.cursor()
    print(b, 'size_mb=', round(p.stat().st_size/1024/1024,2), 'integrity=', cur.execute('pragma integrity_check').fetchone()[0])
    con.close()
rt=root/'runtime_store'
if rt.exists():
    files=sum(1 for x in rt.rglob('*') if x.is_file())
    size=sum(x.stat().st_size for x in rt.rglob('*') if x.is_file())
    print('runtime_store files=', files, 'size_mb=', round(size/1024/1024,2))
else:
    print('runtime_store missing')
PY
