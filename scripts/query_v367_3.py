#!/usr/bin/env python3
import sqlite3, sys

def main():
    db = sys.argv[1] if len(sys.argv) > 1 else 'm367_3_semantic_quarantine_migration.db'
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    cmd = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    if cmd == 'summary':
        for t in ['v3673_semantic_quarantine_sidecar','v3673_text_field_migration_audit','v3673_mainline_semantic_free_view_manifest','v3673_semantic_backwrite_regression','v3673_acceptance_report']:
            print(t, con.execute(f'SELECT COUNT(*) c FROM {t}').fetchone()['c'])
    elif cmd == 'acceptance':
        for r in con.execute('SELECT * FROM v3673_acceptance_report ORDER BY check_id'):
            print(dict(r))
    elif cmd == 'regression':
        for r in con.execute('SELECT * FROM v3673_semantic_backwrite_regression ORDER BY regression_id'):
            print(dict(r))
    elif cmd == 'quarantine':
        for r in con.execute('SELECT sidecar_id, source_table, source_column, payload_kind, status FROM v3673_semantic_quarantine_sidecar LIMIT 20'):
            print(dict(r))
    else:
        raise SystemExit('commands: summary acceptance regression quarantine')
    con.close()
if __name__ == '__main__': main()
