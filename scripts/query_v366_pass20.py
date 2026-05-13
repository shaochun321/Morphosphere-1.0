#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path
DB=Path(__file__).resolve().parent.parent/'outputs'/'v366'/'m366_pass20_native_writer_expansion_rmi_benchmark.db'
if not DB.exists(): DB=Path('/mnt/data/m366_pass20_native_writer_expansion_rmi_benchmark.db')
cmd=sys.argv[1] if len(sys.argv)>1 else 'summary'
con=sqlite3.connect(DB); cur=con.cursor()
if cmd=='summary':
    for row in cur.execute('SELECT * FROM pass20_native_writer_expansion_manifest'):
        print(row)
    print('RMI')
    for row in cur.execute('SELECT variant_id, average_bucket_candidates, max_bucket_candidates, collision_group_count, false_neighbor_group_count, verdict FROM pass20_rmi_query_benchmark'):
        print(row)
elif cmd=='acceptance':
    for row in cur.execute('SELECT check_name,status,observed,requirement FROM pass20_acceptance_report'):
        print(row)
elif cmd=='collisions':
    for row in cur.execute('SELECT variant_id, hash_key, group_size, distinct_dark_zones, distinct_trajectory_windows, false_neighbor_risk FROM pass20_rmi_collision_group ORDER BY variant_id, group_size DESC LIMIT 20'):
        print(row)
elif cmd=='sample':
    for row in cur.execute('SELECT fact_id, process_window_id, information_point_ref, trajectory_window_ref, dark_grid_zone_id, hypernode_id, hyperedge_id FROM pass20_native_writer_emission_expanded LIMIT 10'):
        print(row)
else:
    print('commands: summary acceptance collisions sample')
con.close()
