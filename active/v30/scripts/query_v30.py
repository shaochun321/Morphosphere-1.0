#!/usr/bin/env python3
import sqlite3, argparse, json

def show(title, rows):
    print('\n== '+title+' ==')
    for r in rows:
        print(dict(r))

def main():
    ap=argparse.ArgumentParser(description='Explain v30 macro-node / cluster / confirmed-P renormalization lineage.')
    ap.add_argument('--db', default='outputs/m30.db')
    ap.add_argument('--macro-node-id')
    ap.add_argument('--cluster-id')
    ap.add_argument('--track-id')
    ap.add_argument('--limit', type=int, default=5)
    args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
    if args.macro_node_id:
        rows=cur.execute('select * from v30_macro_node_candidate where macro_node_id=?',(args.macro_node_id,)).fetchall(); show('macro node',rows)
        rows=cur.execute('select * from v30_hierarchical_edge where parent_macro_node_id=? limit ?',(args.macro_node_id,args.limit)).fetchall(); show('children',rows)
        rows=cur.execute('select * from v30_cross_level_attention_request where macro_node_id=?',(args.macro_node_id,)).fetchall(); show('attention requests',rows)
        rows=cur.execute('select * from v30_macro_node_lineage where macro_node_id=?',(args.macro_node_id,)).fetchall(); show('lineage',rows)
    elif args.cluster_id:
        rows=cur.execute('select * from v30_confirmed_p_cluster where cluster_id=?',(args.cluster_id,)).fetchall(); show('cluster',rows)
        rows=cur.execute('select * from v30_effective_information_probe where cluster_id=? limit ?',(args.cluster_id,args.limit)).fetchall(); show('EI probes',rows)
        rows=cur.execute('select * from v30_macro_node_candidate where cluster_id=?',(args.cluster_id,)).fetchall(); show('macro candidates',rows)
    elif args.track_id:
        rows=cur.execute('select * from v30_confirmed_p_cluster where source_track_id=?',(args.track_id,)).fetchall(); show('track clusters',rows)
    else:
        rows=cur.execute('select macro_node_id,source_track_id,confirmed_p_count,effective_information_score,renormalization_readiness,status from v30_macro_node_candidate order by renormalization_readiness desc limit ?',(args.limit,)).fetchall(); show('top macro nodes',rows)
if __name__=='__main__': main()
