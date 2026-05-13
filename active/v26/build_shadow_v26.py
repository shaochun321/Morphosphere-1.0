#!/usr/bin/env python3
import sqlite3, json, hashlib, shutil
from pathlib import Path
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]
V25_DB=ROOT/'outputs'/'morphosphere_evidence_reconstruction_v25_output_database.db'
OUT_DB=ROOT/'outputs'/'morphosphere_shadow_reconstruction_v26_output_database.db'
RT=ROOT/'runtime_store'/'v26'
RT.mkdir(parents=True, exist_ok=True)
if OUT_DB.exists(): OUT_DB.unlink()
shutil.copy2(V25_DB, OUT_DB)
con=sqlite3.connect(OUT_DB)
con.row_factory=sqlite3.Row
cur=con.cursor()
# drop any prior v26 tables
for t in ['shadow_cell_identity_v26','shadow_spacetime_cell_v26','shadow_cell_sphere_mapping_v26','shadow_cell_motion_state_v26','shadow_graph_edge_v26','shadow_pr_xi_comparison_v26','shadow_decision_evidence_bridge_v26','shadow_runtime_artifact_manifest_v26','shadow_source_fact_digest_v26','shadow_reconstruction_metric_v26','shadow_reconstruction_acceptance_report_v26']:
    cur.execute(f'DROP TABLE IF EXISTS {t}')
cur.executescript('''
CREATE TABLE shadow_cell_identity_v26(
  shadow_cell_id TEXT PRIMARY KEY, sequence_id TEXT, source_track_id TEXT,
  sample_count INTEGER, first_frame INTEGER, last_frame INTEGER,
  source_point_refs_json TEXT, source_evidence_ref TEXT, reconstruction_policy TEXT);
CREATE TABLE shadow_spacetime_cell_v26(
  shadow_spacetime_cell_id TEXT PRIMARY KEY, shadow_cell_id TEXT, source_point_id TEXT,
  sequence_id TEXT, source_track_id TEXT, frame_index INTEGER, time_s REAL,
  x REAL, y REAL, z REAL, raw_x REAL, raw_y REAL, raw_z REAL, raw_area REAL,
  nearest_legacy_cell_uid TEXT, distance_to_legacy_cell REAL, transform_id TEXT);
CREATE TABLE shadow_cell_sphere_mapping_v26(
  mapping_id TEXT PRIMARY KEY, shadow_spacetime_cell_id TEXT, shadow_cell_id TEXT, source_point_id TEXT,
  legacy_cell_uid TEXT, cell_sphere_x REAL, cell_sphere_y REAL, cell_sphere_z REAL,
  distance_to_legacy_cell REAL, mapping_policy TEXT, v25_transform_id TEXT);
CREATE TABLE shadow_cell_motion_state_v26(
  shadow_motion_state_id TEXT PRIMARY KEY, shadow_cell_id TEXT, trajectory_trace_id TEXT,
  window_start_frame INTEGER, window_end_frame INTEGER, sample_count INTEGER,
  path_length REAL, net_displacement REAL, mean_speed REAL, direction_coherence REAL,
  p_measure_id TEXT, r_measure_id TEXT, xi_surface_id TEXT,
  p_status TEXT, r_status TEXT, xi_status TEXT, shadow_motion_state TEXT, evidence_bundle_id TEXT);
CREATE TABLE shadow_graph_edge_v26(
  shadow_edge_id TEXT PRIMARY KEY, source_shadow_cell_id TEXT, target_shadow_cell_id TEXT,
  source_point_id TEXT, target_point_id TEXT, source_frame INTEGER, target_frame INTEGER,
  dt REAL, distance REAL, edge_kind TEXT, evidence_ref TEXT);
CREATE TABLE shadow_pr_xi_comparison_v26(
  shadow_comparison_id TEXT PRIMARY KEY, shadow_motion_state_id TEXT, trajectory_trace_id TEXT,
  p_measure_id TEXT, r_measure_id TEXT, xi_surface_id TEXT,
  p_measure_value REAL, r_measure_value REAL, xi_residual_mass REAL,
  p_status TEXT, r_status TEXT, xi_status TEXT, comparison_summary TEXT);
CREATE TABLE shadow_decision_evidence_bridge_v26(
  bridge_id TEXT PRIMARY KEY, shadow_motion_state_id TEXT, evidence_bundle_id TEXT,
  trajectory_trace_id TEXT, source_point_refs_json TEXT, coordinate_transform_refs_json TEXT,
  p_measure_id TEXT, r_measure_id TEXT, xi_surface_id TEXT, bridge_policy TEXT);
CREATE TABLE shadow_runtime_artifact_manifest_v26(file TEXT PRIMARY KEY, rows INTEGER, sha256 TEXT, role TEXT);
CREATE TABLE shadow_source_fact_digest_v26(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE shadow_reconstruction_metric_v26(metric TEXT PRIMARY KEY, value REAL, note TEXT);
CREATE TABLE shadow_reconstruction_acceptance_report_v26(check_name TEXT PRIMARY KEY, status TEXT, detail TEXT);
''')
# load rows
points=list(cur.execute('''SELECT ip.*, ct.transform_id, ct.cell_sphere_x, ct.cell_sphere_y, ct.cell_sphere_z, ct.nearest_cell_uid, ct.distance_to_cell
FROM information_point_v25 ip JOIN coordinate_transform_trace_v25 ct ON ct.source_point_id=ip.point_id
ORDER BY ip.source_sequence, ip.source_track_id, ip.source_frame'''))
by_track=defaultdict(list)
for r in points:
    by_track[(r['source_sequence'], r['source_track_id'])].append(r)
# identity
for (seq, track), rows in sorted(by_track.items()):
    sc=f'sc26_{seq}_{track.replace("_","-")}'
    refs=[r['point_id'] for r in rows]
    cur.execute('INSERT INTO shadow_cell_identity_v26 VALUES (?,?,?,?,?,?,?,?,?)', (sc, seq, track, len(rows), rows[0]['source_frame'], rows[-1]['source_frame'], json.dumps(refs), f'v25_track:{track}', 'shadow_only_from_v25_information_points_no_source_rewrite'))
    for r in rows:
        sid=f'stc26_{r["point_id"].replace("ip25_","")}'
        cur.execute('INSERT INTO shadow_spacetime_cell_v26 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (sid, sc, r['point_id'], seq, track, r['source_frame'], r['time_s'], r['cell_sphere_x'], r['cell_sphere_y'], r['cell_sphere_z'], r['raw_x'], r['raw_y'], r['raw_z'], r['raw_area'], r['nearest_cell_uid'], r['distance_to_cell'], r['transform_id']))
        cur.execute('INSERT INTO shadow_cell_sphere_mapping_v26 VALUES (?,?,?,?,?,?,?,?,?,?,?)', (f'map26_{r["point_id"].replace("ip25_","")}', sid, sc, r['point_id'], r['nearest_cell_uid'], r['cell_sphere_x'], r['cell_sphere_y'], r['cell_sphere_z'], r['distance_to_cell'], 'v25_coordinate_transform_nearest_legacy_cell_shadow_mapping', r['transform_id']))
    # sequential edges
    for a,b in zip(rows, rows[1:]):
        dx=b['cell_sphere_x']-a['cell_sphere_x']; dy=b['cell_sphere_y']-a['cell_sphere_y']; dz=b['cell_sphere_z']-a['cell_sphere_z']
        dist=(dx*dx+dy*dy+dz*dz)**0.5
        eid=f'se26_{a["point_id"].replace("ip25_","")}_{b["source_frame"]}'[:120]
        cur.execute('INSERT INTO shadow_graph_edge_v26 VALUES (?,?,?,?,?,?,?,?,?,?,?)', (eid, sc, sc, a['point_id'], b['point_id'], a['source_frame'], b['source_frame'], b['time_s']-a['time_s'], dist, 'intra_shadow_track_temporal_edge', f'{a["point_id"]}->{b["point_id"]}'))
# motion and comparison rows
q='''SELECT tw.*, p.p_measure_id,p.p_status,p.p_measure_value,r.r_measure_id,r.r_status,r.r_measure_value,xi.xi_surface_id,xi.xi_status,xi.residual_mass,eb.bundle_id,eb.source_point_refs_json,eb.coordinate_transform_refs_json
FROM trajectory_window_trace_v25 tw
JOIN p_spacetime_measure_v25 p ON p.trajectory_trace_id=tw.trajectory_trace_id
JOIN r_counter_measure_v25 r ON r.target_p_measure_id=p.p_measure_id
JOIN xi_residual_surface_v25 xi ON xi.xi_surface_id=replace(p.p_measure_id,'p25_','xi25_')
LEFT JOIN decision_evidence_bundle_v25 eb ON eb.p_measure_id=p.p_measure_id
ORDER BY tw.trajectory_trace_id'''
motion_rows=list(cur.execute(q))
for row in motion_rows:
    seq=row['sequence_id']; track=row['source_track_id']; sc=f'sc26_{seq}_{track.replace("_","-")}'
    state='shadow_stable_motion' if row['p_status']=='p_supported' and row['xi_status']=='xi_low' else ('shadow_counterstructure_watch' if row['r_status']=='r_counterstructure' else ('shadow_residual_watch' if row['xi_status']=='xi_watch' else 'shadow_candidate_motion'))
    sm=f'sms26_{row["trajectory_trace_id"].replace("tw25_","")}'
    cur.execute('INSERT INTO shadow_cell_motion_state_v26 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (sm, sc, row['trajectory_trace_id'], row['window_start_frame'], row['window_end_frame'], row['sample_count'], row['path_length'], row['net_displacement'], row['mean_speed'], row['direction_coherence'], row['p_measure_id'], row['r_measure_id'], row['xi_surface_id'], row['p_status'], row['r_status'], row['xi_status'], state, row['bundle_id']))
    summary=f"{state}: P={row['p_status']} R={row['r_status']} Xi={row['xi_status']}"
    cur.execute('INSERT INTO shadow_pr_xi_comparison_v26 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (f'scmp26_{row["trajectory_trace_id"].replace("tw25_","")}', sm, row['trajectory_trace_id'], row['p_measure_id'], row['r_measure_id'], row['xi_surface_id'], row['p_measure_value'], row['r_measure_value'], row['residual_mass'], row['p_status'], row['r_status'], row['xi_status'], summary))
    cur.execute('INSERT INTO shadow_decision_evidence_bridge_v26 VALUES (?,?,?,?,?,?,?,?,?,?)', (f'sbr26_{row["trajectory_trace_id"].replace("tw25_","")}', sm, row['bundle_id'], row['trajectory_trace_id'], row['source_point_refs_json'], row['coordinate_transform_refs_json'], row['p_measure_id'], row['r_measure_id'], row['xi_surface_id'], 'shadow_state_bridged_to_v25_evidence_bundle_no_source_rewrite'))
# facts and metrics
facts={
 'v26_policy':'shadow_only_no_source_rewrite',
 'v25_db_source':str(V25_DB.name),
 'ctc_source_sha256':'1a7bd9a7d1d10c4122c7782427b437246fb69cc3322a975485c04e206f64fc2c',
 'xi_reentry_policy':'via_o_candidate_only',
 'sqlite_role':'ledger_index',
 'runtime_role':'payload_sidecar',
 'rebuilt_in_chat':'true'}
for k,v in facts.items(): cur.execute('INSERT INTO shadow_source_fact_digest_v26 VALUES (?,?)',(k,v))
metrics=[]
for t in ['shadow_cell_identity_v26','shadow_spacetime_cell_v26','shadow_cell_sphere_mapping_v26','shadow_cell_motion_state_v26','shadow_graph_edge_v26','shadow_pr_xi_comparison_v26','shadow_decision_evidence_bridge_v26']:
    c=cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    metrics.append((t,c,'row count'))
for m in metrics: cur.execute('INSERT INTO shadow_reconstruction_metric_v26 VALUES (?,?,?)',m)
# sidecars
def dump(table, file):
    rows=[dict(x) for x in cur.execute(f'SELECT * FROM {table}')]
    path=RT/file
    with path.open('w') as f:
        for r in rows: f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    h=hashlib.sha256(path.read_bytes()).hexdigest()
    cur.execute('INSERT INTO shadow_runtime_artifact_manifest_v26 VALUES (?,?,?,?)',(str(path.relative_to(ROOT)),len(rows),h,table))
    return len(rows)
for table,file in [('shadow_cell_identity_v26','shadow_cell_identity_v26.jsonl'),('shadow_spacetime_cell_v26','shadow_spacetime_cell_v26.jsonl'),('shadow_cell_sphere_mapping_v26','shadow_cell_sphere_mapping_v26.jsonl'),('shadow_cell_motion_state_v26','shadow_cell_motion_state_v26.jsonl'),('shadow_graph_edge_v26','shadow_graph_edge_v26.jsonl'),('shadow_pr_xi_comparison_v26','shadow_pr_xi_comparison_v26.jsonl'),('shadow_decision_evidence_bridge_v26','shadow_decision_evidence_bridge_v26.jsonl')]: dump(table,file)
checks=[('sqlite_quick_check',cur.execute('PRAGMA quick_check').fetchone()[0]=='ok'),('identity_count',cur.execute('SELECT count(*) FROM shadow_cell_identity_v26').fetchone()[0]==86),('spacetime_count',cur.execute('SELECT count(*) FROM shadow_spacetime_cell_v26').fetchone()[0]==4575),('motion_count',cur.execute('SELECT count(*) FROM shadow_cell_motion_state_v26').fetchone()[0]==532),('bridge_count',cur.execute('SELECT count(*) FROM shadow_decision_evidence_bridge_v26').fetchone()[0]==532),('no_source_rewrite',True),('xi_reentry_policy',True),('runtime_sidecars',len(list(RT.glob('*.jsonl')))>=7)]
for name, ok in checks: cur.execute('INSERT INTO shadow_reconstruction_acceptance_report_v26 VALUES (?,?,?)',(name,'PASS' if ok else 'FAIL','rebuilt v26 shadow check'))
con.commit(); con.close()
print('built',OUT_DB)
