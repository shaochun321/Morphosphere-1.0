#!/usr/bin/env python3
import argparse, sqlite3, json
from pathlib import Path

def dump(label, rows):
    print('\n## '+label)
    if not rows:
        print('(none)'); return
    for r in rows:
        print(json.dumps(dict(r), ensure_ascii=False, indent=2, sort_keys=True))

def main():
    ap=argparse.ArgumentParser(description='Query v29 intervention sandbox records.')
    ap.add_argument('--db', default=str(Path(__file__).resolve().parents[3] / 'outputs' / 'm29.db'))
    ap.add_argument('--proposal-id')
    ap.add_argument('--origin-ref')
    ap.add_argument('--policy-id')
    ap.add_argument('--limit', type=int, default=5)
    args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    if args.proposal_id:
        props=list(con.execute('select * from v29_intervention_proposal where proposal_id=?',(args.proposal_id,)))
    elif args.origin_ref:
        props=list(con.execute('select * from v29_intervention_proposal where origin_ref=? limit ?',(args.origin_ref,args.limit)))
    elif args.policy_id:
        props=list(con.execute('select * from v29_intervention_proposal where policy_ref=? order by priority desc limit ?',(args.policy_id,args.limit)))
    else:
        props=list(con.execute('select * from v29_intervention_proposal order by priority desc limit ?',(args.limit,)))
    dump('proposals', props)
    ids=[r['proposal_id'] for r in props]
    for pid in ids:
        dump('sandbox_replay for '+pid, list(con.execute('select * from v29_sandbox_replay where proposal_id=?',(pid,))))
        dump('effect_report for '+pid, list(con.execute('select * from v29_intervention_effect_report where proposal_id=?',(pid,))))
        dump('action_outcome for '+pid, list(con.execute('select * from v29_action_divergence_outcome where proposal_id=?',(pid,))))
if __name__=='__main__': main()
