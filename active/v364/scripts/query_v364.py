#!/usr/bin/env python3
import argparse, sqlite3
ap=argparse.ArgumentParser()
ap.add_argument('--db', default='outputs/m364.db')
ap.add_argument('--mode', choices=['decisions','bands','xin','contracts'], default='decisions')
ap.add_argument('--limit', type=int, default=5)
args=ap.parse_args()
con=sqlite3.connect(args.db)
if args.mode=='decisions':
    q='SELECT decision_id,r_ref,selected_band_id,decision_class,total_cost,deferred_xin_count FROM v364_coupler_decision_report ORDER BY total_cost LIMIT ?'
elif args.mode=='bands':
    q='SELECT band_id,r_ref,anchor_id,cumulative_discontinuity,ledger_cost,within_p_tunnel FROM v364_r_band_candidate_search LIMIT ?'
elif args.mode=='xin':
    q='SELECT xin_ref,triage_class,residual_mass,foreground_relevance,action_taken FROM v364_xin_triage_policy LIMIT ?'
else:
    q='SELECT contract_id,downgraded_engineering_object,rejected_interpretation FROM v364_downgrade_contract LIMIT ?'
for row in con.execute(q,(args.limit,)):
    print(row)
con.close()
