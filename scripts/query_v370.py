#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',default='m370_native_runtime_prototype.db'); p.add_argument('cmd',choices=['summary','acceptance','samples','trace','roles','rmi']); p.add_argument('--sample'); p.add_argument('--limit',type=int,default=10); a=p.parse_args()
con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row
if a.cmd=='summary':
 print(dict(con.execute('select run_id,run_kind,sample_count,stage_count,boundary_statement from v370_native_runtime_run').fetchone()))
 print([dict(r) for r in con.execute('select status,count(*) n from v370_acceptance_report group by status')])
elif a.cmd=='acceptance':
 [print(dict(r)) for r in con.execute('select * from v370_acceptance_report order by check_id')]
elif a.cmd=='samples':
 [print(dict(r)) for r in con.execute('select sample_id,trajectory_window_ref,sequence_id,role_family,role_proxy,anchor_status from v370_sample_selection order by sample_id limit ?',(a.limit,))]
elif a.cmd=='trace':
 sample=a.sample or con.execute('select sample_id from v370_sample_selection order by sample_id limit 1').fetchone()[0]
 [print(dict(r)) for r in con.execute('select stage_order,stage_name,output_refs_json,status,limitation from v370_stage_trace where sample_id=? order by stage_order',(sample,))]
elif a.cmd=='roles':
 [print(dict(r)) for r in con.execute('select role_family,role_proxy,count(*) n from v370_sample_selection group by role_family,role_proxy order by n desc')]
elif a.cmd=='rmi':
 [print(dict(r)) for r in con.execute('select variant_id,lookup_status,false_neighbor_flag,count(*) n from v370_rmi_lookup_event group by variant_id,lookup_status,false_neighbor_flag')]
