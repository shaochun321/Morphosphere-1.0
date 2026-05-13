#!/usr/bin/env python3
import argparse, sqlite3, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default=str(Path(__file__).resolve().parents[3] / 'outputs' / 'm29.db'))
    args=ap.parse_args()
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row
    ok=con.execute('pragma quick_check(1)').fetchone()[0]
    print('SQLite quick_check:', ok)
    tables=['v29_intervention_proposal','v29_policy_candidate','v29_sandbox_replay','v29_intervention_effect_report','v29_action_divergence_outcome','v29_precision_action_hint','v29_acceptance_report']
    for t in tables:
        print(f'{t}:', con.execute(f'select count(*) from {t}').fetchone()[0])
    bad=[dict(r) for r in con.execute("select * from v29_acceptance_report where status!='PASS'")]
    if ok!='ok' or bad:
        print('FAIL', bad)
        sys.exit(1)
    print('V29_INTERVENTION_POLICY_SANDBOX_ACCEPTANCE: PASS')
if __name__=='__main__': main()
