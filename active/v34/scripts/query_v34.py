#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m34.db'); p.add_argument('--proxy-id'); p.add_argument('--divergence-id'); p.add_argument('--window-id'); p.add_argument('--limit',type=int,default=5); args=p.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
def show(title, rows):
    print('\n## '+title)
    for r in rows:
        print(json.dumps(dict(r),ensure_ascii=False,indent=2))
if args.proxy_id:
    show('proxy registry',cur.execute('select * from v34_proxy_registry where proxy_id=?',(args.proxy_id,)).fetchall())
    show('dependency outgoing',cur.execute('select * from v34_proxy_dependency_edge where parent_proxy_id=? limit ?',(args.proxy_id,args.limit)).fetchall())
    show('entropy bindings',cur.execute('select * from v34_proxy_entropy_binding where proxy_id=? limit ?',(args.proxy_id,args.limit)).fetchall())
elif args.divergence_id:
    show('divergence',cur.execute('select * from v28_divergence_decomposition where divergence_id=?',(args.divergence_id,)).fetchall())
    show('proxy propagation',cur.execute('select * from v34_proxy_propagation_path where terminal_ref_id=?',(args.divergence_id,)).fetchall())
    show('external entropy event',cur.execute('select * from v34_external_entropy_event where source_ref_id=?',(args.divergence_id,)).fetchall())
    show('proxy entropy binding',cur.execute('select b.* from v34_proxy_entropy_binding b join v34_external_entropy_event e on b.entropy_event_ref=e.entropy_event_id where e.source_ref_id=?',(args.divergence_id,)).fetchall())
elif args.window_id:
    show('Noether balance',cur.execute('select * from v34_noether_balance_audit where window_id=?',(args.window_id,)).fetchall())
    show('entropy events',cur.execute('select * from v34_external_entropy_event where window_id=? limit ?',(args.window_id,args.limit)).fetchall())
else:
    show('run manifest',cur.execute('select * from v34_run_manifest').fetchall())
    show('acceptance',cur.execute('select * from v34_acceptance_report').fetchall())
