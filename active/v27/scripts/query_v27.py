#!/usr/bin/env python3
import argparse, sqlite3, json

def rows(con, sql, args=()):
    con.row_factory=sqlite3.Row
    return [dict(r) for r in con.execute(sql,args)]

def shorten(obj, limit):
    if isinstance(obj, str):
        try:
            val=json.loads(obj)
            if isinstance(val, list) and limit is not None: return val[:limit]
            return val
        except Exception: return obj
    return obj

def main():
    ap=argparse.ArgumentParser(description='Query v2.7 reversible measure-field evidence index')
    ap.add_argument('--db', default='outputs/m27.db')
    ap.add_argument('--point-id')
    ap.add_argument('--trajectory-id')
    ap.add_argument('--measure-id')
    ap.add_argument('--limit', type=int, default=5)
    ns=ap.parse_args()
    con=sqlite3.connect(ns.db); con.row_factory=sqlite3.Row
    if ns.point_id:
        q=rows(con,"SELECT * FROM v27_reversible_query_index WHERE query_kind='point' AND target_id=?",(ns.point_id,))
        s=rows(con,"SELECT * FROM v27_measure_point_sample WHERE point_id=? ORDER BY measure_kind",(ns.point_id,))
        print(json.dumps({'query':'point','id':ns.point_id,'index':q,'measure_samples':s},ensure_ascii=False,indent=2))
    elif ns.trajectory_id:
        q=rows(con,"SELECT * FROM v27_reversible_query_index WHERE query_kind='trajectory' AND target_id=?",(ns.trajectory_id,))
        print(json.dumps({'query':'trajectory','id':ns.trajectory_id,'index':q},ensure_ascii=False,indent=2))
    elif ns.measure_id:
        q=rows(con,"SELECT * FROM v27_reversible_query_index WHERE target_id=? OR query_key LIKE ?",(ns.measure_id,'%'+ns.measure_id+'%'))
        print(json.dumps({'query':'measure','id':ns.measure_id,'index':q},ensure_ascii=False,indent=2))
    else:
        ar=rows(con,'SELECT * FROM v27_acceptance_report ORDER BY check_id')
        counts={t: con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['v27_measure_point_sample','v27_measure_field_cell','v27_reversible_query_index','v27_acceptance_report']}
        examples=rows(con,'SELECT query_kind,target_id FROM v27_reversible_query_index ORDER BY query_kind,target_id LIMIT ?', (ns.limit,))
        print(json.dumps({'counts':counts,'acceptance':ar,'examples':examples},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
