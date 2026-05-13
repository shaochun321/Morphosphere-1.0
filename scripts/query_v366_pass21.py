#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('cmd', choices=['summary','repairs','rmi','acceptance']); p.add_argument('--db', default='outputs/v366/m366_pass21_ledger_repair_rmi_scale.db'); p.add_argument('--limit', type=int, default=10); a=p.parse_args()
con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
if a.cmd=='summary':
    for t in ['pass21_ledger_binding_repair','pass21_fk_validation_after_repair','pass21_rmi_mixed_candidate_space','pass21_rmi_query_benchmark_mixed']:
        print(t, con.execute(f'select count(*) c from {t}').fetchone()['c'])
elif a.cmd=='repairs':
    for r in con.execute('select fact_id, trajectory_window_ref, original_ledger_window_ref, repaired_ledger_window_ref, repair_status from pass21_ledger_binding_repair where repair_status != "NO_REPAIR_NEEDED" limit ?', (a.limit,)): print(dict(r))
elif a.cmd=='rmi':
    for r in con.execute('select * from pass21_rmi_query_benchmark_mixed order by variant_id'): print(dict(r))
elif a.cmd=='acceptance':
    for r in con.execute('select * from pass21_acceptance_report'): print(dict(r))
