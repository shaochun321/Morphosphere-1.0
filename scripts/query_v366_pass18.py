#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser()
p.add_argument('--db',default='m366_pass18_native_writer_and_safe_envelope.db')
p.add_argument('cmd',choices=['summary','acceptance','envelope','guards','writer','ctc02'])
p.add_argument('--limit',type=int,default=10)
a=p.parse_args()
con=sqlite3.connect(a.db)
con.row_factory=sqlite3.Row
if a.cmd=='summary':
    for t in ['pass18_run_manifest','pass18_ctc02_replay_summary','pass18_semantic_quarantine_summary']:
        print('##',t)
        for r in con.execute(f'select * from {t}'):
            print(dict(r))
elif a.cmd=='acceptance':
    for r in con.execute('select * from pass18_acceptance_report'):
        print(dict(r))
elif a.cmd=='envelope':
    for r in con.execute('select * from pass18_safe_stress_envelope order by envelope_class, injection_location, intensity_label limit ?', (a.limit,)):
        print(dict(r))
elif a.cmd=='guards':
    for r in con.execute('select * from pass18_p_core_collapse_guard_rule order by collapse_rate desc, collapse_count desc limit ?', (a.limit,)):
        print(dict(r))
elif a.cmd=='writer':
    for r in con.execute('select prototype_id,hypernode_id,hyperedge_id,information_point_ref,trajectory_window_ref,write_status,boundary_note from pass18_l3_native_writer_prototype limit ?', (a.limit,)):
        print(dict(r))
elif a.cmd=='ctc02':
    for r in con.execute('select * from pass18_ctc02_native_shaped_upper_replay_sample limit ?', (a.limit,)):
        print(dict(r))
