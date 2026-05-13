#!/usr/bin/env python3
import sqlite3, sys, os
DB='outputs/v366/m366_build_pass8.db'
cmd=sys.argv[1] if len(sys.argv)>1 else 'summary'
con=sqlite3.connect(DB)
con.row_factory=sqlite3.Row

def rows(sql):
    for r in con.execute(sql):
        print(' | '.join(str(r[k]) for k in r.keys()))
if cmd=='summary':
    print('object_name | object_count | classification')
    rows("select object_name, object_count, classification from pass8_object_counts_summary order by object_name")
elif cmd=='core':
    print('core_object | status | pass8_classification | notes')
    rows("select core_object,status,pass8_classification,notes from pass8_blueprint_core_alignment order by core_object")
elif cmd=='placement':
    print('component | placement | full_chain | core/mainline | external | test | advisory')
    rows("select component_name, placement_class, required_for_full_chain_full_data_run, belongs_to_mainline, belongs_to_external_module, test_or_operability_only, advisory_only from pass8_component_placement_contract order by placement_class, component_name")
elif cmd=='external':
    print('module_or_boundary | placement | rows | read_only | writes_mainline | notes')
    rows("select module_or_boundary, placement_class, row_count, read_only, writes_mainline, notes from pass8_external_module_boundary order by module_or_boundary")
elif cmd=='layers':
    print('order | layer | required | may_bypass | notes')
    rows("select layer_order, layer_name, required_for_full_chain_full_data_run, may_be_bypassed, notes from pass8_full_chain_run_layer_contract order by layer_order")
elif cmd=='acceptance':
    print('check_id | status | check_name | notes')
    rows("select check_id,status,check_name,notes from pass8_acceptance_report order by check_id")
else:
    print('usage: query_v366_pass8.py [summary|core|placement|external|layers|acceptance]')
    sys.exit(1)
