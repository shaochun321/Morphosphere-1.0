#!/usr/bin/env python3
import sqlite3,argparse
p=argparse.ArgumentParser(); p.add_argument('--db',default='m366_pass19_v37_readiness_gate.db'); p.add_argument('cmd',choices=['summary','clauses','rmi','guard','acceptance']); a=p.parse_args(); con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
if a.cmd=='summary':
    [print(t,con.execute(f"select count(*) from {t}").fetchone()[0]) for t in ['pass19_v37_clause_readiness','pass19_native_writer_emission_fact','pass19_rmi_collision_group','pass19_safe_stress_guard_action','pass19_acceptance_report']]
elif a.cmd=='clauses':
    [print(dict(r)) for r in con.execute('select clause_id,clause_name,readiness_level,required_downgrade,blocker from pass19_v37_clause_readiness order by clause_id')]
elif a.cmd=='rmi':
    [print(dict(r)) for r in con.execute('select variant_id,count(*) collision_groups,sum(case when distinct_dark_zones>1 then 1 else 0 end) false_neighbor_groups from pass19_rmi_collision_group group by variant_id')]
elif a.cmd=='guard':
    [print(dict(r)) for r in con.execute('select envelope_class,guard_action,count(*) n from pass19_safe_stress_guard_action group by envelope_class,guard_action order by envelope_class')]
elif a.cmd=='acceptance':
    [print(dict(r)) for r in con.execute('select * from pass19_acceptance_report order by check_id')]
con.close()
