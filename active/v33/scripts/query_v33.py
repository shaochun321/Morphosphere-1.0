#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser(); p.add_argument('--db', default='outputs/m33.db'); p.add_argument('--adapter-id'); p.add_argument('--prediction-id'); p.add_argument('--window-id'); p.add_argument('--limit',type=int,default=5); args=p.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
if args.prediction_id:
    rows=cur.execute('select * from v33_bottom_prediction_event where prediction_event_id=?',(args.prediction_id,)).fetchall()
elif args.adapter_id:
    rows=cur.execute('select * from v33_bottom_prediction_event where adapter_id=? limit ?',(args.adapter_id,args.limit)).fetchall()
elif args.window_id:
    rows=cur.execute('select * from v33_bottom_prediction_event where window_id=? limit ?',(args.window_id,args.limit)).fetchall()
else:
    rows=cur.execute('select * from v33_bottom_prediction_event limit ?',(args.limit,)).fetchall()
print(json.dumps([dict(r) for r in rows],ensure_ascii=False,indent=2))
if rows:
    ids=[r['prediction_event_id'] for r in rows]
    q=','.join('?' for _ in ids)
    maps=cur.execute(f'select * from v33_prediction_to_source_event_mapping where prediction_event_id in ({q})',ids).fetchall()
    print('\nMAPPINGS')
    print(json.dumps([dict(m) for m in maps],ensure_ascii=False,indent=2))
