#!/usr/bin/env python3
import argparse, sqlite3, json

def main():
    ap=argparse.ArgumentParser(description='Query v32 general source events by source-event id, source kind, or source ref.')
    ap.add_argument('--db', default='outputs/m32.db')
    ap.add_argument('--source-event-id')
    ap.add_argument('--source-kind')
    ap.add_argument('--source-ref-id')
    ap.add_argument('--limit', type=int, default=10)
    args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
    where=[]; params=[]
    if args.source_event_id: where.append('e.source_event_id=?'); params.append(args.source_event_id)
    if args.source_kind: where.append('e.source_kind=?'); params.append(args.source_kind)
    if args.source_ref_id: where.append('e.source_ref_id=?'); params.append(args.source_ref_id)
    sql='''SELECT e.*, m.query_status, m.information_point_ref, m.shadow_ref, m.intervention_ref, m.macro_ref, m.policy_ref
           FROM v32_general_source_event e LEFT JOIN v32_adapter_output_mapping m USING(source_event_id)'''
    if where: sql += ' WHERE ' + ' AND '.join(where)
    sql += ' ORDER BY e.source_event_id LIMIT ?'; params.append(args.limit)
    for r in cur.execute(sql, params):
        print(json.dumps(dict(r), ensure_ascii=False, sort_keys=True))
if __name__=='__main__': main()
