#!/usr/bin/env python3
import sqlite3, argparse
p = argparse.ArgumentParser()
p.add_argument('--db', default='m367_5_consolidated_release_candidate.db')
p.add_argument('cmd', nargs='?', default='status', choices=['status','components','gates','warnings','artifacts'])
a = p.parse_args()
con = sqlite3.connect(a.db)
con.row_factory = sqlite3.Row
if a.cmd == 'status':
    print('Morphosphere v36.7.5 consolidated release candidate')
    for r in con.execute('select key,value from v3675_release_manifest order by key'):
        print(f"{r['key']}: {r['value']}")
    print('')
    print('Gate summary:')
    for r in con.execute('select status, count(*) n from v3675_release_gate group by status'):
        print(f"{r['status']}: {r['n']}")
elif a.cmd == 'components':
    for r in con.execute('select component_name,key_rows,status,boundary_note from v3675_component_rollup'):
        print(dict(r))
elif a.cmd == 'gates':
    for r in con.execute('select gate_name,status,observed,required,note from v3675_release_gate'):
        print(dict(r))
elif a.cmd == 'warnings':
    for r in con.execute('select * from v3675_known_warning_index'):
        print(dict(r))
elif a.cmd == 'artifacts':
    for r in con.execute('select path,artifact_type,size_bytes,sha256 from v3675_artifact_manifest'):
        print(dict(r))
con.close()
