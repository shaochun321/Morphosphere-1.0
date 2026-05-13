#!/usr/bin/env python3
import argparse, sqlite3, json
def show(cur,t,w,v,l):
 cols=[x[1] for x in cur.execute(f'pragma table_info({t})')]; rows=cur.execute(f'select * from {t} where {w}=? limit ?',(v,l)).fetchall(); print(f'[{t}] {len(rows)} rows')
 for r in rows: print(json.dumps(dict(zip(cols,r)),ensure_ascii=False,indent=2)[:4000])
def main():
 p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m31.db'); p.add_argument('--policy-id'); p.add_argument('--cycle-id'); p.add_argument('--proposal-id'); p.add_argument('--limit',type=int,default=3); a=p.parse_args(); con=sqlite3.connect(a.db); cur=con.cursor()
 if a.policy_id: show(cur,'v31_policy_belief_state','policy_id',a.policy_id,a.limit); show(cur,'v31_active_loop_cycle','policy_id',a.policy_id,a.limit); show(cur,'v31_policy_update','policy_id',a.policy_id,a.limit)
 elif a.cycle_id: show(cur,'v31_active_loop_cycle','cycle_id',a.cycle_id,a.limit); show(cur,'v31_action_observation_trace','cycle_id',a.cycle_id,a.limit)
 elif a.proposal_id: show(cur,'v31_active_loop_cycle','proposal_id',a.proposal_id,a.limit); show(cur,'v31_action_observation_trace','proposal_id',a.proposal_id,a.limit)
 else:
  for t in ['v31_policy_belief_state','v31_loop_summary','v31_guardrail_audit']:
   print('\n--',t)
   for r in cur.execute(f'select * from {t} limit {a.limit}'): print(r)
if __name__=='__main__': main()
