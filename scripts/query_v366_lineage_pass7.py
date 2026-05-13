#!/usr/bin/env python3
import sqlite3, argparse, json, sys

def rows(cur, sql, args=()):
    cur.execute(sql,args); cols=[d[0] for d in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

ap=argparse.ArgumentParser(description='Query Morphosphere v36.6 Pass7 native-write readiness surface')
ap.add_argument('--db', default='outputs/v366/m366_build_pass7.db')
sub=ap.add_subparsers(dest='cmd', required=True)
sub.add_parser('status'); sub.add_parser('health'); sub.add_parser('debt'); sub.add_parser('contracts'); sub.add_parser('plan'); sub.add_parser('recipes')
p=sub.add_parser('candidates'); p.add_argument('--limit', type=int, default=5)
p=sub.add_parser('sql'); p.add_argument('query')
args=ap.parse_args(); con=sqlite3.connect(args.db); cur=con.cursor()
if args.cmd=='status':
    out={}
    for t in ['pass7_native_write_contract','pass7_upstream_writer_upgrade_plan','pass7_directness_debt_index','pass7_native_write_candidate_index','pass7_module_readiness_matrix']:
        out[t]=cur.execute(f'select count(*) from {t}').fetchone()[0]
    out['acceptance']=rows(cur,'select check_name,status,observed_value,required_value from pass7_acceptance_report')
    print(json.dumps(out, ensure_ascii=False, indent=2))
elif args.cmd=='health':
    print(json.dumps(rows(cur,'select * from pass7_module_readiness_matrix order by module_name'), ensure_ascii=False, indent=2))
elif args.cmd=='debt':
    print(json.dumps(rows(cur,'select * from pass7_directness_debt_index order by priority, object_family'), ensure_ascii=False, indent=2))
elif args.cmd=='contracts':
    print(json.dumps(rows(cur,'select * from pass7_native_write_contract order by migration_priority, contract_id'), ensure_ascii=False, indent=2))
elif args.cmd=='plan':
    print(json.dumps(rows(cur,'select * from pass7_upstream_writer_upgrade_plan order by priority, plan_id'), ensure_ascii=False, indent=2))
elif args.cmd=='recipes':
    print(json.dumps(rows(cur,'select * from pass7_query_recipe_library order by recipe_id'), ensure_ascii=False, indent=2))
elif args.cmd=='candidates':
    print(json.dumps(rows(cur,'select * from pass7_native_write_candidate_index limit ?', (args.limit,)), ensure_ascii=False, indent=2))
elif args.cmd=='sql':
    print(json.dumps(rows(cur,args.query), ensure_ascii=False, indent=2))
con.close()
