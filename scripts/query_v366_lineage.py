#!/usr/bin/env python3
import sqlite3, argparse, json, sys

def rows(cur, sql, args=()):
    cur.execute(sql,args); cols=[d[0] for d in cur.description]
    return [dict(zip(cols,r)) for r in cur.fetchall()]

ap=argparse.ArgumentParser(description="Query Morphosphere v36.6 Pass6 lineage surface")
ap.add_argument("--db", default="outputs/v366/m366_build_pass6.db")
sub=ap.add_subparsers(dest="cmd", required=True)
sub.add_parser("status"); sub.add_parser("health")
p=sub.add_parser("samples"); p.add_argument("--limit", type=int, default=5)
p=sub.add_parser("trace"); p.add_argument("--id", required=True)
p=sub.add_parser("sql"); p.add_argument("query")
args=ap.parse_args(); con=sqlite3.connect(args.db); cur=con.cursor()
if args.cmd=="status":
    out={t:cur.execute(f"select count(*) from {t}").fetchone()[0] for t in ["pass6_lineage_trace_index","pass6_backtrace_sample","pass6_module_health_score","pass6_collaboration_edge_index"]}
    out["acceptance"]=rows(cur,"select check_name,status,observed_value,required_value from pass6_acceptance_report")
    print(json.dumps(out, ensure_ascii=False, indent=2))
elif args.cmd=="health":
    print(json.dumps(rows(cur,"select * from pass6_module_health_score order by health_score desc"), ensure_ascii=False, indent=2))
elif args.cmd=="samples":
    r=rows(cur,"select * from pass6_backtrace_sample limit ?", (args.limit,))
    for d in r:
        try: d["path_json"]=json.loads(d["path_json"])
        except Exception: pass
    print(json.dumps(r, ensure_ascii=False, indent=2))
elif args.cmd=="trace":
    r=rows(cur,"select * from pass6_lineage_trace_index where trace_id=? or process_window_id=? or trajectory_trace_id=? or source_ref=? limit 1", (args.id,args.id,args.id,args.id))
    if not r:
        print(json.dumps({"found":False,"id":args.id}, ensure_ascii=False, indent=2)); sys.exit(1)
    d=r[0]
    try: d["trace_json"]=json.loads(d["trace_json"])
    except Exception: pass
    print(json.dumps(d, ensure_ascii=False, indent=2))
elif args.cmd=="sql":
    print(json.dumps(rows(cur,args.query), ensure_ascii=False, indent=2))
con.close()
