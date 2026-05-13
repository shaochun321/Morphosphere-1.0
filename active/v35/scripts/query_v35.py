#!/usr/bin/env python3
import argparse, sqlite3, json
ap=argparse.ArgumentParser(); ap.add_argument('--db',default='outputs/m35.db'); ap.add_argument('--limit',type=int,default=5); ap.add_argument('--novelty',action='store_true'); args=ap.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
if args.novelty:
    q='''select p.proposal_id,p.target_region_ref,a.conclusion,a.mean_SNR_path,a.integrated_anomaly_mass,pr.verdict from v35_attentional_path_integral_audit a join v35_attention_proposal p on p.proposal_id=a.proposal_id join v35_attention_performance_report pr on pr.path_integral_id=a.path_integral_id where a.novelty_candidate=1 order by a.mean_SNR_path desc limit ?'''
else:
    q='''select t.region_id,t.attention_tension,t.tension_rank,p.proposal_id,a.conclusion,a.mean_SNR_path,pr.verdict from v35_attention_tension_map t join v35_attention_proposal p on p.target_region_ref=t.region_id join v35_attentional_path_integral_audit a on a.proposal_id=p.proposal_id join v35_attention_performance_report pr on pr.path_integral_id=a.path_integral_id order by t.tension_rank limit ?'''
for r in cur.execute(q,(args.limit,)).fetchall(): print(json.dumps(dict(r),ensure_ascii=False))
