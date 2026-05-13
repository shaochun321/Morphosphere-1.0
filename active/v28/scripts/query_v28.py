#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser(description='Query v28 shadow-evidence divergence records')
p.add_argument('--db', default='outputs/m28.db')
g=p.add_mutually_exclusive_group(required=True)
for name in ['evidence-edge-id','shadow-edge-id','alignment-id','divergence-id','confirmed-p-id','penalty-id','surprise-id','point-id']:
    g.add_argument('--'+name)
p.add_argument('--limit', type=int, default=5); args=p.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
def dump(title, rows):
    print('\n## '+title)
    for r in rows: print(json.dumps(dict(r),ensure_ascii=False,indent=2))
def q(sql,params=()): return con.execute(sql,params).fetchall()
if args.evidence_edge_id:
    dump('evidence edge',q('select * from v28_evidence_edge where evidence_edge_id=?',(args.evidence_edge_id,)))
    dump('alignments',q('select * from v28_shadow_evidence_alignment where evidence_edge_id=? limit ?',(args.evidence_edge_id,args.limit)))
elif args.shadow_edge_id:
    dump('shadow edge',q('select * from v28_shadow_edge where shadow_edge_id=?',(args.shadow_edge_id,)))
    dump('penalties',q('select * from v28_shadow_overreach_penalty where shadow_edge_id=? limit ?',(args.shadow_edge_id,args.limit)))
elif args.alignment_id: dump('alignment',q('select * from v28_shadow_evidence_alignment where alignment_id=?',(args.alignment_id,)))
elif args.divergence_id: dump('divergence',q('select * from v28_divergence_decomposition where divergence_id=?',(args.divergence_id,)))
elif args.confirmed_p_id: dump('confirmed P',q('select * from v28_confirmed_p_structure where confirmed_p_id=?',(args.confirmed_p_id,)))
elif args.penalty_id: dump('overreach penalty',q('select * from v28_shadow_overreach_penalty where penalty_id=?',(args.penalty_id,)))
elif args.surprise_id: dump('surprise Xi',q('select * from v28_evidence_surprise_xi where surprise_id=?',(args.surprise_id,)))
elif args.point_id:
    dump('evidence edges involving point',q('select * from v28_evidence_edge where point_a_id=? or point_b_id=? limit ?',(args.point_id,args.point_id,args.limit)))
    dump('shadow edges involving point',q('select * from v28_shadow_edge where source_point_id=? or target_point_id=? limit ?',(args.point_id,args.point_id,args.limit)))
