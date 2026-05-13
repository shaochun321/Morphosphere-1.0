#!/usr/bin/env python3
import sqlite3, argparse
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/v366/m366_pass16_source_rerun_and_anchor.db'); p.add_argument('cmd',choices=['summary','stress','seq','anchor','accept']); args=p.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor()
if args.cmd=='summary':
    for t in ['pass16_source_rerun_case','pass16_source_level_rerun_result','pass16_ctc02_overlay_projection','pass16_measure_anchor_hash_registry']:
        print(t, cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0])
elif args.cmd=='stress':
    for r in cur.execute('SELECT scenario_id,result_count,role_changed_count,p_to_r_count,r_or_p_to_xin_count,p_core_collapse_count,verdict FROM pass16_source_rerun_summary ORDER BY scenario_id'): print(r)
elif args.cmd=='seq':
    for r in cur.execute('SELECT sequence_id,window_count,mean_p,mean_r,mean_xin,mean_attention_tension,effective_attention_share,projected_rband_share FROM pass16_sequence_overlay_comparison ORDER BY sequence_id'): print(r)
elif args.cmd=='anchor':
    for r in cur.execute('SELECT * FROM pass16_anchor_directness_summary ORDER BY tier'): print(r)
elif args.cmd=='accept':
    for r in cur.execute('SELECT * FROM pass16_acceptance_report ORDER BY check_id'): print(r)
