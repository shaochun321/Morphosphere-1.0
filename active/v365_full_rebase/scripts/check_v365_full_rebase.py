#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db', default='outputs/m365_full_rebase.db'); args=p.parse_args()
conn=sqlite3.connect(args.db); cur=conn.cursor()
fail=[]
for table in ['rebase_artifact_identity','rebase_component_inventory','rebase_version_coverage','rebase_boundary_audit','rebase_acceptance_report']:
    n=cur.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    print(f'{table}: {n}')
    if n==0: fail.append(table)
acc=cur.execute("SELECT status, COUNT(*) FROM rebase_acceptance_report GROUP BY status").fetchall()
print('acceptance:', dict(acc))
fail += [r[0] for r in cur.execute("SELECT check_id FROM rebase_acceptance_report WHERE status!='PASS'").fetchall()]
fail += [r[0] for r in cur.execute("SELECT audit_id FROM rebase_boundary_audit WHERE status!='PASS'").fetchall()]
identity=dict(cur.execute('SELECT key,value FROM rebase_artifact_identity').fetchall())
if identity.get('artifact_type')!='FULL_LINEAGE_REBASE_CANDIDATE': fail.append('artifact_type')
if fail:
    print('FAIL', fail); sys.exit(1)
print('PASS v36.5 full-lineage rebase candidate')
