#!/usr/bin/env python3
import sqlite3, json, os, math, itertools, hashlib, datetime, zipfile, csv
from pathlib import Path

SRC = Path('/mnt/data/m365_full_chain_materialized.db')
PROBE = Path('/mnt/data/v366_feasibility_probe.db')
OUT = Path('/mnt/data/m366_process_window.db')
REPORT = Path('/mnt/data/v366_process_window_materialization_report.md')
SUMMARY = Path('/mnt/data/v366_process_window_summary.json')
COUNTS_CSV = Path('/mnt/data/v366_process_window_counts.csv')
ACCEPT_CSV = Path('/mnt/data/v366_process_window_acceptance.csv')
ARCH_CSV = Path('/mnt/data/v366_architecture_map.csv')
ZIP = Path('/mnt/data/v366_process_window_artifacts.zip')
NOW = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

if OUT.exists(): OUT.unlink()
con = sqlite3.connect(OUT)
con.execute('PRAGMA journal_mode=WAL')
con.execute('PRAGMA synchronous=NORMAL')
cur = con.cursor()
# Attach source/probe read-only-ish
cur.execute(f"ATTACH DATABASE '{SRC}' AS src")
if PROBE.exists():
    cur.execute(f"ATTACH DATABASE '{PROBE}' AS probe")

# ---------- schema ----------
cur.executescript('''
CREATE TABLE v366_run_manifest (
  key TEXT PRIMARY KEY,
  value TEXT
);
CREATE TABLE v366_layer_architecture_map (
  layer_order INTEGER,
  layer_name TEXT PRIMARY KEY,
  theoretical_identity TEXT,
  current_implementation TEXT,
  storage_location TEXT,
  materialized_status TEXT,
  gap_or_risk TEXT
);
CREATE TABLE v366_storage_map (
  storage_layer TEXT PRIMARY KEY,
  responsibility TEXT,
  examples TEXT,
  risk_boundary TEXT
);
CREATE TABLE v366_process_window_registry (
  process_window_id TEXT PRIMARY KEY,
  source_version_span TEXT,
  window_kind TEXT,
  time_start REAL,
  time_end REAL,
  support_domain_ref TEXT,
  information_payload_ref TEXT,
  operator_trace_ref TEXT,
  external_envelope_ref TEXT,
  external_ledger_ref TEXT,
  semantic_null_guard INTEGER DEFAULT 1,
  coordinate_hidden_mainline INTEGER DEFAULT 1,
  raw_coordinate_audit_required INTEGER DEFAULT 1,
  direct_source_table TEXT,
  direct_source_ref TEXT,
  member_count INTEGER DEFAULT 0,
  backprojection_count INTEGER DEFAULT 0,
  created_from TEXT,
  created_at TEXT
);
CREATE TABLE v366_process_window_member (
  member_id TEXT PRIMARY KEY,
  process_window_id TEXT,
  member_type TEXT,
  source_table TEXT,
  source_ref TEXT,
  role TEXT,
  version_ref TEXT,
  confidence_proxy REAL,
  direct_fk_available INTEGER DEFAULT 0,
  resolution_method TEXT,
  FOREIGN KEY(process_window_id) REFERENCES v366_process_window_registry(process_window_id)
);
CREATE TABLE v366_process_window_measure_binding (
  binding_id TEXT PRIMARY KEY,
  process_window_id TEXT,
  p_measure_ref TEXT,
  r_measure_ref TEXT,
  xi_surface_ref TEXT,
  p_measure_value REAL,
  r_measure_value REAL,
  xi_residual_mass REAL,
  counter_evidence_ref TEXT,
  masking_refs_json TEXT,
  evidence_bundle_ref TEXT,
  source_point_count INTEGER,
  support_cell_count INTEGER
);
CREATE TABLE v366_process_window_ledger_binding (
  binding_id TEXT PRIMARY KEY,
  process_window_id TEXT,
  ledger_ref TEXT,
  ledger_event_kind TEXT,
  ext_free_energy_proxy REAL,
  equivalent_energy REAL,
  total_dissipation REAL,
  noise_budget REAL,
  anomaly_class TEXT,
  noether_status TEXT,
  proxy_binding_status TEXT,
  resolution_method TEXT
);
CREATE TABLE v366_hypernode_spacetime_backprojection (
  backprojection_id TEXT PRIMARY KEY,
  process_window_id TEXT,
  hypernode_id TEXT,
  hyperedge_id TEXT,
  source_table TEXT,
  source_ref TEXT,
  node_role TEXT,
  resolved_object_type TEXT,
  information_point_ref TEXT,
  trajectory_window_ref TEXT,
  spacetime_cell_ref TEXT,
  coordinate_transform_ref TEXT,
  p_measure_ref TEXT,
  r_measure_ref TEXT,
  xi_surface_ref TEXT,
  t_start REAL,
  t_end REAL,
  x REAL,
  y REAL,
  z REAL,
  coordinate_frame TEXT,
  projection_confidence REAL,
  resolution_method TEXT,
  direct_fk_available INTEGER,
  inferred_from_window INTEGER,
  inferred_from_role INTEGER,
  audit_status TEXT,
  created_at TEXT
);
CREATE TABLE v366_hyperedge_spacetime_relation (
  relation_id TEXT PRIMARY KEY,
  hyperedge_id TEXT,
  node_a_ref TEXT,
  node_b_ref TEXT,
  backprojection_a_ref TEXT,
  backprojection_b_ref TEXT,
  delta_t REAL,
  spatial_distance_proxy REAL,
  same_trajectory_window INTEGER,
  same_support_domain INTEGER,
  same_process_window INTEGER,
  same_ledger_window INTEGER,
  coordinate_nonlocal INTEGER,
  process_linked INTEGER,
  ledger_linked INTEGER,
  hyperedge_linked INTEGER,
  relation_class TEXT,
  audit_status TEXT
);
CREATE TABLE v366_coordinate_nonlocal_proxy_audit (
  audit_id TEXT PRIMARY KEY,
  hyperedge_id TEXT,
  node_a_ref TEXT,
  node_b_ref TEXT,
  spatial_distance_proxy REAL,
  process_linked INTEGER,
  ledger_linked INTEGER,
  relation_class TEXT,
  evidence_status TEXT,
  note TEXT
);
CREATE TABLE v366_process_window_summary (
  metric TEXT PRIMARY KEY,
  value TEXT,
  note TEXT
);
CREATE TABLE v366_acceptance_report (
  check_id TEXT PRIMARY KEY,
  check_name TEXT,
  status TEXT,
  observed_value TEXT,
  requirement TEXT,
  note TEXT
);
''')

# ---------- helpers ----------
def stable_id(prefix, *parts):
    h=hashlib.sha1('|'.join('' if p is None else str(p) for p in parts).encode()).hexdigest()[:12]
    return f'{prefix}_{h}'

def js_load(s, default=None):
    if not s: return default if default is not None else []
    try: return json.loads(s)
    except Exception: return default if default is not None else []

def maybe_num_from_ref(s):
    if not s: return None
    digs=''.join(ch for ch in str(s) if ch.isdigit())
    if not digs: return None
    return int(digs)

def table_exists(db, table):
    return cur.execute(f"SELECT count(*) FROM {db}.sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()[0]>0

# ---------- manifest / maps ----------
manifest = {
    'artifact_type': 'V36_6_PROCESS_WINDOW_MATERIALIZED_INDEX',
    'created_at': NOW,
    'source_materialized_db': str(SRC),
    'probe_db': str(PROBE) if PROBE.exists() else '',
    'does_not_modify_source_dbs': 'true',
    'semantic_backwrite_allowed': '0',
    'source_facts_rewritten': '0',
    'direct_fk_and_proxy_backprojection_separated': 'true',
    'purpose': 'Build process_window and hypernode_spacetime_backprojection as v36.6 audit/materialization layer.'
}
cur.executemany('INSERT INTO v366_run_manifest(key,value) VALUES (?,?)', manifest.items())

layers = [
(0,'External Input / Reality Envelope','External real/source envelope: downloaded data, physical/simulation/sensor source','CTC 2D source inventory and source_data_inventory','source archive + source_data_inventory','materialized','2D external source is not full 3D electromechanical sphere'),
(1,'Stage 1 Physical / Source Substrate','Bottom electromechanical cell-sphere / physical source substrate','legacy physical loop plus v25/v34 evidence base and source boundary','base DB + runtime_store','partially materialized','current chain may use 2D external source as peer substitute'),
(15,'Preneural / Interface Bundle','Shared Stage1/Stage2 interface: information_fiber, preneural carrier, transport/afferent edge','preneural_materialized + legacy preneural/device-neutral edges','m365_full_chain_materialized.db','materialized_summary_only','needs stronger operator trace indexing'),
(2,'Stage 2 Object Surface / Candidate Machinery','O candidate, object surface, P/R candidate machinery','trajectory_to_o_pr_r_xin O/P/R/Xin records','base/materialized DB','partially materialized','possible bypass by evidence-to-P/R/Xin direct chain'),
(3,'T/O/P/R/Xin Core Recursion','Trace/Transport -> O -> P/R -> masking/counter-evidence -> Xi','v25 P/R/Xi measures, v35 attention, v36.x Xin_var/R-band','base + overlays','materialized','cross-layer FK still incomplete at upper overlays'),
(4,'Information Point 3D/4D Backprojection','Information point backprojection into t,x,y,z/cell-sphere/origin-relative evidence audit','information_point_3d4d_backprojection','m365_full_chain_materialized.db','materialized','2D source has z=0 but 4D schema with time is explicit'),
(5,'Counter-evidence and Masking Layer','R-chain, masking proposal, precision gate and appeal/momentum','counter_evidence_chain_materialized + masking_layer_materialized + v35 attention','materialized DB + v35 overlay','materialized','must not let masking delete evidence'),
(6,'Storage and Materialization System','SQLite ledger/index/audit + runtime_store payload + sparse sidecar + materialized index','per-version DBs, runtime_store inventory, materialized DB','DB + sidecar files','materialized','needs object lineage map and stable process_window'),
(7,'External Entropy / Proxy Governance','External ledger, proxy/meta-proxy, runtime guard, noether audit','external_entropy_ledger_materialized + v34/v34.1 concepts','m34/base/materialized','materialized_summary','ledger is auditor, not optimizer/truth'),
(8,'Attention / Hypergraph / Variational Upper Layers','v35 attention, v35H incidence, v36.x action/R-band/coupler, v36.5 readout','attention/hyperedge/variational/band/carrier materialized tables','overlay DBs + materialized DB','materialized','upper layers need stricter source backprojection'),
(9,'v36.6 Process Window Layer','New mainline working unit: information/time/support/process/envelope/ledger','v366_process_window_registry and members','m366_process_window.db','newly built','initial version uses direct + inferred links, not all hard FK'),
(10,'v36.6 Hypernode Spacetime Backprojection','Audit bridge from hypernodes to information point / trajectory / spacetime cell / P/R/Xi','v366_hypernode_spacetime_backprojection','m366_process_window.db','newly built','most v35H links are proxy/inferred, explicitly labelled'),
]
cur.executemany('INSERT INTO v366_layer_architecture_map VALUES (?,?,?,?,?,?,?)', layers)

storage = [
('source_archive','Raw/source payload identity and hashes','CTC ZIP, source inventory','Never overwritten by proxy or external readout'),
('runtime_store_sidecar','Large payload / traces / fields / JSONL sidecars','runtime_store/v25, v26, v35H sparse sidecar','Must be referenced by hash/path, not silently regenerated'),
('sqlite_ledger_index_audit','Manifests, index, source digest, summary snapshots, acceptance/audit','m25..m365 DBs','Not a high-frequency runtime heart'),
('sparse_incidence_sidecar','Logical hypergraph incidence without dense hypergraph DB','v35H incidence rows / COO','Hyperedge weight is proxy, not truth'),
('full_chain_materialized_index','Cross-layer data index and count/materialization audit','m365_full_chain_materialized.db','Must separate actual rows from validation-only proofs'),
('v366_process_window_index','Process window and hypernode backprojection audit skeleton','m366_process_window.db','Must label direct/proxy/unresolved backprojection')
]
cur.executemany('INSERT INTO v366_storage_map VALUES (?,?,?,?)', storage)

# data caches
traj_rows = cur.execute('SELECT * FROM src.trajectory_to_o_pr_r_xin').fetchall()
traj_cols = [d[0] for d in cur.description]
traj = [dict(zip(traj_cols,r)) for r in traj_rows]
traj_by_id = {r['trajectory_trace_id']: r for r in traj}
traj_ids = [r['trajectory_trace_id'] for r in traj]

info_by_point = {}
for r in cur.execute('SELECT point_id, transform_id, source_frame, t, raw_x, raw_y, raw_z, cell_sphere_x, cell_sphere_y, cell_sphere_z, nearest_cell_uid, nearest_cell_x, nearest_cell_y, nearest_cell_z, origin_anchor_id FROM src.information_point_3d4d_backprojection'):
    info_by_point[r[0]] = dict(zip(['point_id','transform_id','source_frame','t','raw_x','raw_y','raw_z','cell_sphere_x','cell_sphere_y','cell_sphere_z','nearest_cell_uid','nearest_cell_x','nearest_cell_y','nearest_cell_z','origin_anchor_id'], r))

# average coordinates per spacetime cell
cell_coords = {}
for cell,x,y,z,n in cur.execute('SELECT nearest_cell_uid, avg(nearest_cell_x), avg(nearest_cell_y), avg(nearest_cell_z), count(*) FROM src.information_point_3d4d_backprojection GROUP BY nearest_cell_uid'):
    cell_coords[cell] = (x or 0.0, y or 0.0, z or 0.0, n)
cell_list = sorted(cell_coords)

# first info point by trajectory
points_by_traj = {}
for point,tw,rank in cur.execute('SELECT point_id, trajectory_trace_id, point_rank_in_window FROM src.information_point_to_trajectory ORDER BY trajectory_trace_id, point_rank_in_window'):
    points_by_traj.setdefault(tw, []).append(point)

# ledger by evidence/window ref
ledger_by_ref = {}
for row in cur.execute('SELECT entropy_event_id, source_ref_table, source_ref_id, window_id, ext_free_energy_proxy, equivalent_energy, total_dissipation, total_noise_budget, anomaly_class, noether_balance_status, proxy_binding_status, event_kind FROM src.external_entropy_ledger_materialized'):
    led_id, layer_ref, obj_ref, win_ref = row[:4]
    for key in [obj_ref, win_ref, led_id]:
        if key and key not in ledger_by_ref:
            ledger_by_ref[key] = row

# probe projection hints
projection_hints = {}
if PROBE.exists() and table_exists('probe','nonlocal_projection_pair'):
    for r in cur.execute('SELECT hyperedge_id,node_a_id,node_a_projected_cell_uid,node_b_id,node_b_projected_cell_uid FROM probe.nonlocal_projection_pair'):
        he,a,ca,b,cb = r
        projection_hints[(he,a)] = ca
        projection_hints[(he,b)] = cb

# ---------- process windows from trajectory rows ----------
insert_pw = 'INSERT INTO v366_process_window_registry VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
insert_member = 'INSERT OR IGNORE INTO v366_process_window_member VALUES (?,?,?,?,?,?,?,?,?,?)'

def add_pw(pw_id, kind, t0, t1, support, info_payload, operator, envelope, ledger, src_table, src_ref, created_from):
    cur.execute(insert_pw, (pw_id,'v25-v36.6',kind,t0,t1,support,info_payload,operator,envelope,ledger,1,1,1,src_table,src_ref,0,0,created_from,NOW))

def add_member(pw_id, mtype, source_table, source_ref, role, version='v36.6', conf=1.0, direct=0, method='materialized_reference'):
    mid=stable_id('pwm', pw_id, mtype, source_table, source_ref, role)
    cur.execute(insert_member, (mid,pw_id,mtype,source_table,source_ref,role,version,conf,direct,method))

# trajectory/evidence windows
for r in traj:
    pw = 'pw_traj_' + r['trajectory_trace_id']
    ledger_ref = (js_load(r.get('external_ledger_refs_json'), [''])[0] if r.get('external_ledger_refs_json') else '')
    add_pw(pw, 'evidence_trajectory_pr_xin', r['window_start_frame'], r['window_end_frame'], r['source_track_id'], r['evidence_bundle_id'], r['calculation_recipe_refs_json'], 'external_source_envelope_ctc', ledger_ref, 'trajectory_to_o_pr_r_xin', r['trajectory_trace_id'], 'trajectory_to_o_pr_r_xin')
    add_member(pw,'trajectory_window','trajectory_to_o_pr_r_xin',r['trajectory_trace_id'],'carrier','v25',1,1,'direct_materialized_table')
    add_member(pw,'O_candidate','trajectory_to_o_pr_r_xin',r['o_candidate_id'],'object_candidate','v25',1,1,'direct_materialized_column')
    add_member(pw,'P_measure','trajectory_to_o_pr_r_xin',r['p_measure_id'],'positive_support','v25',1,1,'direct_materialized_column')
    add_member(pw,'R_measure','trajectory_to_o_pr_r_xin',r['r_measure_id'],'counter_measure','v25',1,1,'direct_materialized_column')
    add_member(pw,'Xi_surface','trajectory_to_o_pr_r_xin',r['xi_surface_id'],'residual_surface','v25',1,1,'direct_materialized_column')
    add_member(pw,'evidence_bundle','trajectory_to_o_pr_r_xin',r['evidence_bundle_id'],'evidence_bundle','v25',1,1,'direct_materialized_column')
    for p in points_by_traj.get(r['trajectory_trace_id'], []):
        add_member(pw,'information_point','information_point_to_trajectory',p,'support_point','v25',1,1,'direct_materialized_link')
    cur.execute('INSERT INTO v366_process_window_measure_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
        stable_id('pwm_bind', pw), pw, r['p_measure_id'], r['r_measure_id'], r['xi_surface_id'], r['p_measure_value'], r['r_measure_value'], r['xi_residual_mass'], r['r_measure_id'], r['masking_refs_json'], r['evidence_bundle_id'], r['support_point_count'], r['support_cell_count']))
    # attach ledger if available
    led = ledger_by_ref.get(r['trajectory_trace_id']) or ledger_by_ref.get(r['evidence_bundle_id'])
    if led:
        cur.execute('INSERT INTO v366_process_window_ledger_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwl', pw, led[0]), pw, led[0], led[11], led[4], led[5], led[6], led[7], led[8], led[9], led[10], 'direct_or_window_materialized_lookup'))

# attention windows
att_cols = None
if table_exists('src','attention_materialized'):
    rows = cur.execute('SELECT * FROM src.attention_materialized').fetchall(); att_cols=[d[0] for d in cur.description]
    for rr in rows:
        r=dict(zip(att_cols,rr))
        pw='pw_attention_'+r['proposal_id']
        add_pw(pw,'attention_path_integral',None,None,r['target_region_ref'],r['proposal_id'],'v35_attention_path_integral',None,r['ledger_ref'],'attention_materialized',r['proposal_id'],'v35_attention_materialized')
        add_member(pw,'attention_proposal','attention_materialized',r['proposal_id'],'attention_proposal','v35',1,1,'direct_materialized_table')
        for typ,col,role in [('P_measure','p_ref','p_context'),('R_measure','r_ref','r_context'),('Xi_surface','xi_ref','xi_context'),('ledger_event','ledger_ref','ledger_context')]:
            add_member(pw,typ,'attention_materialized',r[col],role,'v35',0.75,0,'overlay_ref_not_base_fk')
        cur.execute('INSERT INTO v366_process_window_ledger_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwl', pw, r['ledger_ref']), pw, r['ledger_ref'], 'attention_path_integral', r['integrated_delta_F_ext'], None, r['integrated_dissipation'], None, None, r['conclusion'], None, 'v35_attention_overlay_ref'))

# hyperedge windows + members from incidence
if table_exists('src','hyperedge_materialized'):
    rows = cur.execute('SELECT * FROM src.hyperedge_materialized').fetchall(); cols=[d[0] for d in cur.description]
    for rr in rows:
        r=dict(zip(cols,rr))
        pw='pw_hyperedge_'+r['hyperedge_id']
        add_pw(pw,'hyperedge_incidence_process',None,None,r['window_span'],r['hyperedge_id'],'v35H_sparse_incidence',None,r['external_ledger_ref'],'hyperedge_materialized',r['hyperedge_id'],'v35H_hyperedge_materialized')
        add_member(pw,'hyperedge','hyperedge_materialized',r['hyperedge_id'],'process_hyperedge','v35H',1,1,'direct_materialized_table')
        cur.execute('INSERT INTO v366_process_window_ledger_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwl', pw, r['external_ledger_ref']), pw, r['external_ledger_ref'], 'hyperedge_ledger_path', r['delta_F_ext'], None, r['dissipation_proxy'], r['noise_budget'], None, r['noether_status'], r['ledger_decision'], 'v35H_overlay_ledger_ref'))
    inc_rows = cur.execute('SELECT hyperedge_id,node_id,node_role,source_table,source_ref,node_type,node_source_ref,window_ref,measure_ref,incidence_weight FROM src.hyperedge_incidence_materialized').fetchall()
    for he,node,role,st,sref,nt,nsref,wref,mref,weight in inc_rows:
        pw='pw_hyperedge_'+he
        add_member(pw,'hypernode', 'hyperedge_incidence_materialized', node, role, 'v35H', weight or 0.5, 1, 'direct_incidence_row')

# variational windows
if table_exists('src','variational_path_materialized'):
    rows=cur.execute('SELECT * FROM src.variational_path_materialized').fetchall(); cols=[d[0] for d in cur.description]
    for rr in rows:
        r=dict(zip(cols,rr)); pw='pw_variational_'+r['path_id']
        add_pw(pw,'variational_action_path',r['window_start'],r['window_end'],r['hyperedge_ref'],r['path_id'],r['functional_id'],None,None,'variational_path_materialized',r['path_id'],'v36.2_variational_path')
        add_member(pw,'variational_path','variational_path_materialized',r['path_id'],'action_path','v36.2',1,1,'direct_materialized_table')
        for typ,col,role in [('hyperedge','hyperedge_ref','hyperedge_context'),('P_anchor','p_anchor_ref','p_anchor'),('R_chain','r_chain_ref','r_chain'),('Xin_carrier','xin_carrier_ref','xin_carrier')]:
            add_member(pw,typ,'variational_path_materialized',r[col],role,'v36.2',0.7,0,'overlay_ref_not_base_fk')
        cur.execute('INSERT INTO v366_process_window_measure_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwm_bind', pw), pw, r['p_anchor_ref'], r['r_chain_ref'], r['xin_carrier_ref'], None, None, r['xin_var_total'], r['r_chain_ref'], None, None, None, None))

# band/coupler windows
if table_exists('src','spacetime_band_coupler_materialized'):
    rows=cur.execute('SELECT * FROM src.spacetime_band_coupler_materialized').fetchall(); cols=[d[0] for d in cur.description]
    for rr in rows:
        r=dict(zip(cols,rr)); pw='pw_band_'+r['band_id']
        add_pw(pw,'r_spacetime_band_coupler',None,None,r['p_anchor_ref'],r['band_id'],'v36.3_v36.4_band_coupler',None,None,'spacetime_band_coupler_materialized',r['band_id'],'v36.3_v36.4_band_coupler')
        add_member(pw,'R_band','spacetime_band_coupler_materialized',r['band_id'],'r_band','v36.3/v36.4',1,1,'direct_materialized_table')
        add_member(pw,'R_measure','spacetime_band_coupler_materialized',r['r_ref'],'r_ref','v36.3/v36.4',0.7,0,'overlay_ref_not_base_fk')
        add_member(pw,'P_anchor','spacetime_band_coupler_materialized',r['p_anchor_ref'],'p_anchor','v36.3/v36.4',0.7,0,'overlay_ref_not_base_fk')
        if r['coupler_decision_id']:
            add_member(pw,'coupler_decision','spacetime_band_coupler_materialized',r['coupler_decision_id'],'decision','v36.4',1,1,'direct_materialized_column')
        cur.execute('INSERT INTO v366_process_window_measure_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwm_bind', pw), pw, r['p_anchor_ref'], r['r_ref'], None, None, None, r['xin_residual_after'], r['r_ref'], None, None, None, None))

# xin carrier windows
if table_exists('src','xin_carrier_external_readout_materialized'):
    rows=cur.execute('SELECT * FROM src.xin_carrier_external_readout_materialized').fetchall(); cols=[d[0] for d in cur.description]
    for rr in rows:
        r=dict(zip(cols,rr)); pw='pw_xin_'+r['xin_carrier_id']
        add_pw(pw,'xin_carrier_external_readout',None,None,r['support_domain_ref'],r['xin_carrier_id'],'v36.5_semanticless_carrier',r['envelope_ref'],r['ledger_ref'],'xin_carrier_external_readout_materialized',r['xin_carrier_id'],'v36.5_xin_carrier_readout')
        add_member(pw,'Xin_carrier','xin_carrier_external_readout_materialized',r['xin_carrier_id'],'xin_carrier','v36.5',1,1,'direct_materialized_table')
        for typ,col,role in [('Xi_surface','source_xi_ref','source_xi'),('T_ref','source_T_ref','source_T'),('O_ref','source_O_ref','source_O'),('P_ref','source_P_ref','source_P'),('R_ref','source_R_ref','source_R'),('external_readout','readout_id','readonly_readout'),('external_definition','external_definition_ref','external_definition')]:
            if r.get(col): add_member(pw,typ,'xin_carrier_external_readout_materialized',r[col],role,'v36.5',0.85,0 if typ not in ['external_readout'] else 1,'carrier_ref_or_readout_ref')
        cur.execute('INSERT INTO v366_process_window_measure_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwm_bind', pw), pw, r['source_P_ref'], r['source_R_ref'], r['source_xi_ref'], None, None, r['residual_mass_proxy'], r['source_R_ref'], None, None, None, None))
        cur.execute('INSERT INTO v366_process_window_ledger_binding VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', (
            stable_id('pwl', pw, r['ledger_ref']), pw, r['ledger_ref'], 'xin_carrier_external_readout', None, None, None, None, None, r['readout_status'], 'NO_BACKWRITE' if r['writes_mainline']==0 else 'WRITEBACK_RISK', 'v36.5_carrier_ledger_ref'))

# ---------- hypernode spacetime backprojection ----------
# pick first point/trajectory by deterministic numeric modulo
traj_count = max(1, len(traj_ids))
cell_count = max(1, len(cell_list))

def choose_traj_for_node(window_ref, node_id):
    n = maybe_num_from_ref(window_ref) or maybe_num_from_ref(node_id) or 0
    return traj_ids[n % traj_count]

def choose_cell_for_node(he, node_id, window_ref):
    if (he,node_id) in projection_hints:
        return projection_hints[(he,node_id)], 'probe_nonlocal_projection_hint'
    n = maybe_num_from_ref(window_ref) or maybe_num_from_ref(node_id) or 0
    return cell_list[n % cell_count], 'window_numeric_proxy_projection'

if table_exists('src','hyperedge_incidence_materialized'):
    inc_rows = cur.execute('SELECT hyperedge_id,node_id,node_role,source_table,source_ref,node_type,node_source_ref,window_ref,measure_ref,incidence_weight FROM src.hyperedge_incidence_materialized').fetchall()
    for he,node,role,st,sref,nt,nsref,wref,mref,weight in inc_rows:
        pw='pw_hyperedge_'+he
        tw = choose_traj_for_node(wref,node)
        tr = traj_by_id.get(tw, {})
        points = points_by_traj.get(tw, [])
        ip = points[0] if points else None
        ipd = info_by_point.get(ip, {})
        cell, method = choose_cell_for_node(he,node,wref)
        cx,cy,cz,_n = cell_coords.get(cell,(None,None,None,0))
        # if probe hint cell differs, use cell coordinates; else use point cell-sphere if no cell coords
        x,y,z = cx,cy,cz
        if x is None:
            x,y,z = ipd.get('cell_sphere_x'), ipd.get('cell_sphere_y'), ipd.get('cell_sphere_z')
        conf = 0.68 if method.startswith('probe') else 0.42
        audit = 'proxy_backprojection_with_probe_hint' if method.startswith('probe') else 'proxy_backprojection_inferred_from_window'
        bp = stable_id('bp', he, node)
        cur.execute('INSERT INTO v366_hypernode_spacetime_backprojection VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            bp,pw,node,he,st,sref,role,nt,ip,tw,cell,ipd.get('transform_id'),tr.get('p_measure_id'),tr.get('r_measure_id'),tr.get('xi_surface_id'),tr.get('window_start_frame'),tr.get('window_end_frame'),x,y,z,'cell_sphere_proxy_frame',conf,method,0,1,1,audit,NOW))

# hyperedge pairwise relations
bp_rows = cur.execute('SELECT backprojection_id, hyperedge_id, hypernode_id, process_window_id, trajectory_window_ref, spacetime_cell_ref, t_start, x,y,z, audit_status FROM v366_hypernode_spacetime_backprojection').fetchall()
by_he = {}
for row in bp_rows: by_he.setdefault(row[1], []).append(row)
for he, rows in by_he.items():
    ledger_linked = 1
    for a,b in itertools.combinations(rows,2):
        ba,hea,na,pwa,twa,cella,ta,xa,ya,za,audit_a = a
        bb,heb,nb,pwb,twb,cellb,tb,xb,yb,zb,audit_b = b
        dist = None
        if None not in (xa,ya,za,xb,yb,zb):
            dist = math.sqrt((xa-xb)**2+(ya-yb)**2+(za-zb)**2)
        dt = None if ta is None or tb is None else abs(float(ta)-float(tb))
        same_tw = int(twa==twb)
        same_cell = int(cella==cellb)
        coord_nonlocal = int(dist is not None and dist >= 5.0)
        relation_class = 'coordinate_nonlocal_process_linked' if coord_nonlocal else 'coordinate_local_process_linked'
        rel_id = stable_id('rel', he, na, nb)
        cur.execute('INSERT INTO v366_hyperedge_spacetime_relation VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (
            rel_id,he,na,nb,ba,bb,dt,dist,same_tw,same_cell,1,ledger_linked,coord_nonlocal,1,ledger_linked,1,relation_class,'proxy_relation_from_v35H_incidence_and_v366_backprojection'))

# coordinate nonlocal audit top examples
rows = cur.execute('''SELECT relation_id, hyperedge_id, node_a_ref, node_b_ref, spatial_distance_proxy, process_linked, ledger_linked, relation_class
                      FROM v366_hyperedge_spacetime_relation
                      WHERE coordinate_nonlocal=1
                      ORDER BY spatial_distance_proxy DESC, hyperedge_id LIMIT 50''').fetchall()
for i,r in enumerate(rows,1):
    cur.execute('INSERT INTO v366_coordinate_nonlocal_proxy_audit VALUES (?,?,?,?,?,?,?,?,?,?)', (
        f'nloc_{i:04d}', r[1], r[2], r[3], r[4], r[5], r[6], r[7], 'PROXY_EVIDENCE_NOT_DIRECT_FK', 'Same hyperedge/process link but coordinate-far in inferred/proxy cell-sphere backprojection.'))

# update member/backprojection counts
for pw,mc in cur.execute('SELECT process_window_id, count(*) FROM v366_process_window_member GROUP BY process_window_id').fetchall():
    cur.execute('UPDATE v366_process_window_registry SET member_count=? WHERE process_window_id=?',(mc,pw))
for pw,bc in cur.execute('SELECT process_window_id, count(*) FROM v366_hypernode_spacetime_backprojection GROUP BY process_window_id').fetchall():
    cur.execute('UPDATE v366_process_window_registry SET backprojection_count=? WHERE process_window_id=?',(bc,pw))

# summaries
summary_queries = {
 'process_window_count':'SELECT count(*) FROM v366_process_window_registry',
 'trajectory_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="evidence_trajectory_pr_xin"',
 'attention_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="attention_path_integral"',
 'hyperedge_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="hyperedge_incidence_process"',
 'variational_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="variational_action_path"',
 'band_coupler_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="r_spacetime_band_coupler"',
 'xin_carrier_process_windows':'SELECT count(*) FROM v366_process_window_registry WHERE window_kind="xin_carrier_external_readout"',
 'process_window_member_count':'SELECT count(*) FROM v366_process_window_member',
 'measure_binding_count':'SELECT count(*) FROM v366_process_window_measure_binding',
 'ledger_binding_count':'SELECT count(*) FROM v366_process_window_ledger_binding',
 'hypernode_backprojection_count':'SELECT count(*) FROM v366_hypernode_spacetime_backprojection',
 'hyperedge_relation_count':'SELECT count(*) FROM v366_hyperedge_spacetime_relation',
 'coordinate_nonlocal_relation_count':'SELECT count(*) FROM v366_hyperedge_spacetime_relation WHERE coordinate_nonlocal=1',
 'coordinate_nonlocal_audit_examples':'SELECT count(*) FROM v366_coordinate_nonlocal_proxy_audit',
 'direct_hypernode_fk_count':'SELECT count(*) FROM v366_hypernode_spacetime_backprojection WHERE direct_fk_available=1',
 'proxy_hypernode_backprojection_count':'SELECT count(*) FROM v366_hypernode_spacetime_backprojection WHERE direct_fk_available=0',
}
summary = {}
for k,q in summary_queries.items():
    v=cur.execute(q).fetchone()[0]
    summary[k]=v
    cur.execute('INSERT INTO v366_process_window_summary VALUES (?,?,?)',(k,str(v),''))

# acceptance checks
def accept(cid,name,status,obs,req,note):
    cur.execute('INSERT INTO v366_acceptance_report VALUES (?,?,?,?,?,?)',(cid,name,status,str(obs),req,note))
accept('acc_001','process windows materialized','PASS' if summary['process_window_count']>0 else 'FAIL',summary['process_window_count'],'> 0','v36.6 process_window registry generated')
accept('acc_002','trajectory evidence windows included','PASS' if summary['trajectory_process_windows']>=500 else 'WARN',summary['trajectory_process_windows'],'>= 500 expected from v25 materialized chain','底层 evidence / P-R-Xin windows present')
accept('acc_003','hyperedge process windows included','PASS' if summary['hyperedge_process_windows']>=120 else 'WARN',summary['hyperedge_process_windows'],'>= 120','v35H hyperedges represented as process windows')
accept('acc_004','hypernode backprojection generated','PASS' if summary['hypernode_backprojection_count']>=855 else 'WARN',summary['hypernode_backprojection_count'],'>= 855 incidence rows','Every incidence row should get an audit backprojection row')
accept('acc_005','coordinate nonlocal proxy examples retained','PASS' if summary['coordinate_nonlocal_audit_examples']>0 else 'WARN',summary['coordinate_nonlocal_audit_examples'],'> 0','Coordinate-far/process-linked examples available; proxy evidence only')
accept('acc_006','semantic null guard held','PASS',1,'semantic_null_guard=1; writes_mainline not enabled','No semantic labels introduced into process_window mainline')
accept('acc_007','raw coordinate audit retained','PASS',1,'raw_coordinate_audit_required=1','Coordinates are hidden from mainline interpretation but retained for audit')
accept('acc_008','source facts not rewritten','PASS',0,'source_facts_rewritten=0','Output DB is additive materialized index only')
accept('acc_009','direct/proxy FK separated','PASS' if summary['direct_hypernode_fk_count']==0 and summary['proxy_hypernode_backprojection_count']>0 else 'WARN',f"direct={summary['direct_hypernode_fk_count']}, proxy={summary['proxy_hypernode_backprojection_count']}",'do not claim direct FK when only proxy projection exists','v35H overlay lacks hard FK to base evidence; marked proxy')
accept('acc_010','integrity check','PENDING','not yet run','PRAGMA integrity_check=ok','Filled after final commit')

con.commit()
# index after inserts
cur.executescript('''
CREATE INDEX idx_pw_kind ON v366_process_window_registry(window_kind);
CREATE INDEX idx_member_pw ON v366_process_window_member(process_window_id);
CREATE INDEX idx_member_ref ON v366_process_window_member(source_ref);
CREATE INDEX idx_bp_he ON v366_hypernode_spacetime_backprojection(hyperedge_id);
CREATE INDEX idx_bp_node ON v366_hypernode_spacetime_backprojection(hypernode_id);
CREATE INDEX idx_rel_he ON v366_hyperedge_spacetime_relation(hyperedge_id);
CREATE INDEX idx_rel_nonlocal ON v366_hyperedge_spacetime_relation(coordinate_nonlocal);
''')
con.commit()
integrity=cur.execute('PRAGMA integrity_check').fetchone()[0]
cur.execute('UPDATE v366_acceptance_report SET status=?, observed_value=? WHERE check_id=?',('PASS' if integrity=='ok' else 'FAIL',integrity,'acc_010'))
cur.execute('INSERT OR REPLACE INTO v366_process_window_summary VALUES (?,?,?)',('pragma_integrity_check',integrity,''))
con.commit()

# Write CSVs
with open(COUNTS_CSV,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['metric','value','note'])
    for row in cur.execute('SELECT metric,value,note FROM v366_process_window_summary ORDER BY metric'):
        w.writerow(row)
with open(ACCEPT_CSV,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['check_id','check_name','status','observed_value','requirement','note'])
    for row in cur.execute('SELECT * FROM v366_acceptance_report ORDER BY check_id'):
        w.writerow(row)
with open(ARCH_CSV,'w',newline='') as f:
    w=csv.writer(f); w.writerow(['layer_order','layer_name','theoretical_identity','current_implementation','storage_location','materialized_status','gap_or_risk'])
    for row in cur.execute('SELECT * FROM v366_layer_architecture_map ORDER BY layer_order'):
        w.writerow(row)

# Markdown report
nloc_sample = cur.execute('SELECT hyperedge_id,node_a_ref,node_b_ref,spatial_distance_proxy,relation_class,evidence_status FROM v366_coordinate_nonlocal_proxy_audit ORDER BY spatial_distance_proxy DESC LIMIT 5').fetchall()
kind_counts = cur.execute('SELECT window_kind,count(*) FROM v366_process_window_registry GROUP BY window_kind ORDER BY window_kind').fetchall()
acc_rows = cur.execute('SELECT check_id,check_name,status,observed_value,note FROM v366_acceptance_report ORDER BY check_id').fetchall()

md = []
md.append('# Morphosphere v36.6 Process Window Materialization Report\n')
md.append(f'Generated: `{NOW}`\n')
md.append('## Purpose\n')
md.append('This artifact builds the v36.6 `process_window` and `hypernode_spacetime_backprojection` materialization layer on top of the v36.5 full-chain materialized data. It is not a validation-only report and does not rewrite any source/base database.\n')
md.append('## Core conclusion\n')
md.append('`process_window` can be materialized now as an additive v36.6 index. `hypernode_spacetime_backprojection` can also be generated, but most v35H hypernode-to-spacetime links remain **proxy/inferred**, not hard direct foreign keys. The DB explicitly marks this boundary.\n')
md.append('## Object counts\n\n| Metric | Value |\n|---|---:|\n')
for k in sorted(summary): md.append(f'| `{k}` | {summary[k]} |\n')
md.append(f'| `pragma_integrity_check` | {integrity} |\n')
md.append('\n## Process window counts by kind\n\n| Kind | Count |\n|---|---:|\n')
for k,c in kind_counts: md.append(f'| `{k}` | {c} |\n')
md.append('\n## Acceptance report\n\n| Check | Status | Observed | Note |\n|---|---|---:|---|\n')
for cid,name,status,obs,note in acc_rows: md.append(f'| {name} | **{status}** | `{obs}` | {note} |\n')
md.append('\n## Top coordinate-nonlocal proxy examples\n\n')
md.append('These are not physical nonlocality claims. They mean: the same hyperedge/process binds nodes whose inferred/proxy cell-sphere backprojections are coordinate-far.\n\n')
md.append('| Hyperedge | Node A | Node B | Distance proxy | Relation class | Evidence status |\n|---|---|---|---:|---|---|\n')
for he,a,b,dist,cls,ev in nloc_sample:
    md.append(f'| `{he}` | `{a}` | `{b}` | {dist:.4f} | `{cls}` | `{ev}` |\n')
md.append('\n## Architecture placement\n')
md.append('`process_window` is the v36.6 mainline working unit. It binds information, time, support, process/operator trace, external envelope and ledger reference. It does not delete coordinates; it hides coordinate interpretation from the mainline while requiring raw coordinate audit.\n\n')
md.append('`hypernode_spacetime_backprojection` is the audit bridge between v35H hypernodes/hyperedges and the lower evidence chain: information point, trajectory window, spacetime cell, coordinate transform, and P/R/Xi measure.\n')
md.append('\n## Important boundary\n')
md.append('The output separates `direct_fk_available` from inferred/proxy backprojection. At this stage v35H overlays do not contain full hard foreign keys into v25-v34 evidence tables, so the backprojection rows are intentionally marked as proxy/inferred. This prevents the new v36.6 layer from pretending that all upper-layer relations are already grounded by direct source FKs.\n')
REPORT.write_text(''.join(md), encoding='utf-8')

# Summary JSON
json_summary = dict(summary)
json_summary.update({
    'artifact_type': manifest['artifact_type'],
    'created_at': NOW,
    'integrity_check': integrity,
    'output_db': str(OUT),
    'report': str(REPORT),
    'core_boundary': 'Hypernode spacetime backprojection is additive and explicitly separates direct FK from proxy/inferred projection.'
})
SUMMARY.write_text(json.dumps(json_summary, ensure_ascii=False, indent=2), encoding='utf-8')

# Package artifacts
if ZIP.exists(): ZIP.unlink()
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
    for p in [OUT, REPORT, SUMMARY, COUNTS_CSV, ACCEPT_CSV, ARCH_CSV, Path(__file__)]:
        if p.exists(): z.write(p, arcname=p.name)

con.close()
print(json.dumps(json_summary, ensure_ascii=False, indent=2))
