#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db', default='outputs/m365_full_rebase.db'); p.add_argument('--table', default='coverage'); p.add_argument('--limit', type=int, default=30); args=p.parse_args()
conn=sqlite3.connect(args.db); cur=conn.cursor()
lookup={
 'identity':'rebase_artifact_identity',
 'components':'rebase_component_inventory',
 'coverage':'rebase_version_coverage',
 'boundaries':'rebase_boundary_audit',
 'acceptance':'rebase_acceptance_report',
}
t=lookup.get(args.table,args.table)
for row in cur.execute(f'SELECT * FROM {t} LIMIT ?', (args.limit,)):
    print(row)
