#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path
DB=Path(__file__).resolve().parent/'m368_1_mainline_functional_integration.db'
if len(sys.argv)>1 and sys.argv[1]=='--db':
    DB=Path(sys.argv[2]); args=sys.argv[3:]
else:
    args=sys.argv[1:]
cmd=args[0] if args else 'summary'
con=sqlite3.connect(DB); con.row_factory=sqlite3.Row; cur=con.cursor()
def show(sql):
    for r in cur.execute(sql): print(dict(r))
if cmd=='summary':
    show("select * from v3681_acceptance_report")
elif cmd=='stages':
    show("select stage_order, stage_name, stage_class, changes_information_state, mathematical_proxy from v3681_mainline_stage_contract order by stage_order")
elif cmd=='modules':
    show("select module_name, category, changes_information_state, role_summary from v3681_module_role_classification order by category, module_name")
elif cmd=='effects':
    show("select source_module, target_state, effect_type, mathematical_relation, evidence_count from v3681_module_effect_matrix")
elif cmd=='formulas':
    show("select proxy_name, formula, source_layer, limitation from v3681_mathematical_proxy_catalog")
elif cmd=='priorities':
    show("select priority_rank, build_item, reason, expected_output from v3681_next_build_priority order by priority_rank")
else:
    print('commands: summary, stages, modules, effects, formulas, priorities')
