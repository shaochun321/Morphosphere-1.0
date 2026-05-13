#!/usr/bin/env python3
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
for name in ['restore_inputs.json','module_status.json','db_manifest.json','missing_source_report.json']:
    p=root/'manifests'/name
    print('\n== '+name+' ==')
    data=json.loads(p.read_text())
    print('items:', len(data))
    for item in data[:40]:
        if name=='restore_inputs.json':
            print(f"- {item['label']}: {item['python_files']} py ({item['status']})")
        elif name=='db_manifest.json':
            print(f"- {item['path']}: {item['sqlite_quick_check']} {item.get('table_count')}")
        else:
            print(f"- {item.get('path')}: {item.get('status')}")
print('\nSee docs/SOURCE_LINEAGE.md')
