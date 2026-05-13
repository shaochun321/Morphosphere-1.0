#!/usr/bin/env python3
import json, sqlite3, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
errors=[]
for rel in ['manifests/restore_inputs.json','manifests/module_status.json','manifests/missing_source_report.json','manifests/db_manifest.json']:
    if not (root/rel).exists(): errors.append('missing '+rel)
try:
    restore=json.loads((root/'manifests/restore_inputs.json').read_text())
    if len(restore) < 6: errors.append('too few restored inputs')
except Exception as e: errors.append('restore_inputs unreadable '+str(e))
try:
    dbm=json.loads((root/'manifests/db_manifest.json').read_text())
    for item in dbm:
        if item.get('sqlite_quick_check') != 'ok': errors.append('db not ok '+item.get('path','?'))
except Exception as e: errors.append('db_manifest unreadable '+str(e))
if errors:
    print('V27R_SHORT_ACCEPTANCE: FAIL')
    for e in errors: print('- '+e)
    sys.exit(1)
print('V27R_SHORT_ACCEPTANCE: PASS')
print('root folder: m')
print('legacy source restored for audit; not auto-active')
