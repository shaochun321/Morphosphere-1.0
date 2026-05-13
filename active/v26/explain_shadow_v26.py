#!/usr/bin/env python3
import argparse, sqlite3, json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
ap=argparse.ArgumentParser()
ap.add_argument('--id', required=True, help='shadow motion state id, trajectory_trace_id, or v25 p/r/xi id')
ap.add_argument('--db', default=str(root/'outputs'/'morphosphere_shadow_reconstruction_v26_output_database.db'))
ap.add_argument('--limit-points', type=int, default=5)
args=ap.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
q='''SELECT sms.*, cmp.comparison_summary, br.source_point_refs_json, br.coordinate_transform_refs_json
FROM shadow_cell_motion_state_v26 sms
LEFT JOIN shadow_pr_xi_comparison_v26 cmp ON cmp.shadow_motion_state_id=sms.shadow_motion_state_id
LEFT JOIN shadow_decision_evidence_bridge_v26 br ON br.shadow_motion_state_id=sms.shadow_motion_state_id
WHERE sms.shadow_motion_state_id=? OR sms.trajectory_trace_id=? OR sms.p_measure_id=? OR sms.r_measure_id=? OR sms.xi_surface_id=? LIMIT 1'''
row=cur.execute(q,(args.id,args.id,args.id,args.id,args.id)).fetchone()
if not row:
    raise SystemExit('not found: '+args.id)
print('shadow_motion_state_id:',row['shadow_motion_state_id'])
print('shadow_cell_id:',row['shadow_cell_id'])
print('trajectory_trace_id:',row['trajectory_trace_id'])
print('window:',row['window_start_frame'],'-',row['window_end_frame'])
print('state:',row['shadow_motion_state'])
print('P/R/Xi:',row['p_measure_id'],row['r_measure_id'],row['xi_surface_id'])
print('statuses:',row['p_status'],row['r_status'],row['xi_status'])
print('summary:',row['comparison_summary'])
pts=json.loads(row['source_point_refs_json'] or '[]')[:args.limit_points]
print('points:',pts)
for pid in pts:
    p=cur.execute('SELECT source_sequence, source_frame, source_track_id, raw_x, raw_y, raw_area FROM information_point_v25 WHERE point_id=?',(pid,)).fetchone()
    if p: print(' ',pid,dict(p))
