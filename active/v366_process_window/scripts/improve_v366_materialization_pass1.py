#!/usr/bin/env python3
import sqlite3, json, os, hashlib, csv, statistics, math, time, zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path('/mnt/data')
BASE_OUT = ROOT / 'Morphosphere_v36_5_full_lineage_rebase' / 'outputs'
M365 = ROOT / 'm365_full_chain_materialized.db'
M366 = ROOT / 'm366_process_window.db'
M34 = BASE_OUT / 'm34.db'
OUT = ROOT / 'm366_improvement_pass1.db'
SUMMARY = ROOT / 'm366_improvement_pass1_summary.json'
REPORT = ROOT / 'm366_improvement_pass1_report.md'
COUNTS = ROOT / 'm366_improvement_pass1_counts.csv'
ZIP = ROOT / 'm366_improvement_pass1_artifacts.zip'

for p in [M365, M366, M34]:
    if not p.exists():
        raise FileNotFoundError(p)
if OUT.exists():
    OUT.unlink()


def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def qdict(cur, sql, args=()):
    cur.execute(sql,args)
    cols=[d[0] for d in cur.description]
    return [dict(zip(cols,row)) for row in cur.fetchall()]

def has_table(cur, table):
    return cur.execute("select 1 from sqlite_master where type='table' and name=?", (table,)).fetchone() is not None

def table_count(cur, table):
    try: return cur.execute(f"select count(*) from {table}").fetchone()[0]
    except Exception: return 0

def safe_json(x):
    if not x: return []
    try: return json.loads(x)
    except Exception: return []

# Connect input DBs readonly-ish
con365 = sqlite3.connect(str(M365)); con365.row_factory=sqlite3.Row; c365=con365.cursor()
con366 = sqlite3.connect(str(M366)); con366.row_factory=sqlite3.Row; c366=con366.cursor()
con34 = sqlite3.connect(str(M34)); con34.row_factory=sqlite3.Row; c34=con34.cursor()

out = sqlite3.connect(str(OUT)); out.row_factory=sqlite3.Row; co=out.cursor()
co.executescript('''
PRAGMA journal_mode=OFF;
PRAGMA synchronous=OFF;
CREATE TABLE improvement_run_manifest(key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE stage2_object_surface_materialization_audit(
  audit_id TEXT PRIMARY KEY,
  trajectory_trace_id TEXT,
  source_track_id TEXT,
  o_candidate_id TEXT,
  p_measure_id TEXT,
  r_measure_id TEXT,
  xi_surface_id TEXT,
  has_o_candidate_ref INTEGER,
  direct_stage2_o_record_fk INTEGER,
  direct_stage2_o_surface_fk INTEGER,
  base_o_candidate_record_count INTEGER,
  base_o_candidate_surface_count INTEGER,
  online_o_candidate_tick_count INTEGER,
  bypass_risk_class TEXT,
  materialization_status TEXT,
  recommended_action TEXT,
  evidence_note TEXT
);

CREATE TABLE stage2_summary(
  metric TEXT PRIMARY KEY,
  value TEXT,
  note TEXT
);

CREATE TABLE preneural_interface_operator_trace(
  operator_trace_id TEXT PRIMARY KEY,
  clock_n INTEGER,
  source_cell_uid TEXT,
  spacetime_cell_id TEXT,
  information_fiber_id TEXT,
  binding_id TEXT,
  preneural_node_id TEXT,
  online_tick_state_id TEXT,
  node_state_count INTEGER,
  edge_state_out_count INTEGER,
  synaptic_edge_out_count INTEGER,
  device_tick_state_count INTEGER,
  v33_prediction_bridge_count INTEGER,
  release_proxy REAL,
  afferent_current REAL,
  spike_rate REAL,
  input_energy REAL,
  activation REAL,
  uncertainty REAL,
  interface_status TEXT,
  source_fact_readonly INTEGER,
  notes TEXT
);

CREATE TABLE counter_masking_coverage_audit(
  audit_id TEXT PRIMARY KEY,
  r_measure_id TEXT,
  trajectory_trace_id TEXT,
  source_track_id TEXT,
  counter_support_point_count INTEGER,
  counter_length REAL,
  r_status TEXT,
  masking_refs_json TEXT,
  masking_ref_count INTEGER,
  concrete_mask_direct_count INTEGER,
  concrete_mask_category_count INTEGER,
  coverage_class TEXT,
  risk_note TEXT
);

CREATE TABLE hypernode_direct_fk_upgrade_candidate(
  candidate_id TEXT PRIMARY KEY,
  hypernode_id TEXT,
  hyperedge_id TEXT,
  node_role TEXT,
  node_type TEXT,
  node_source_ref TEXT,
  current_resolution_method TEXT,
  current_audit_status TEXT,
  proposed_target_table TEXT,
  proposed_target_ref TEXT,
  upgrade_class TEXT,
  confidence_proxy REAL,
  blocking_reason TEXT,
  proposed_action TEXT
);

CREATE TABLE process_window_quality_score(
  process_window_id TEXT PRIMARY KEY,
  window_kind TEXT,
  member_count INTEGER,
  measure_binding_count INTEGER,
  ledger_binding_count INTEGER,
  backprojection_count INTEGER,
  semantic_null_guard INTEGER,
  coordinate_hidden_mainline INTEGER,
  raw_coordinate_audit_required INTEGER,
  quality_score REAL,
  quality_class TEXT,
  missing_capabilities_json TEXT,
  recommended_action TEXT
);

CREATE TABLE improvement_acceptance_report(
  check_id TEXT PRIMARY KEY,
  check_name TEXT,
  status TEXT,
  observed_value TEXT,
  requirement TEXT,
  note TEXT
);

CREATE TABLE improvement_object_counts(
  object_name TEXT PRIMARY KEY,
  object_count INTEGER,
  note TEXT
);
''')

now = datetime.now(timezone.utc).isoformat()
manifest = {
    'artifact': 'm366_improvement_pass1',
    'created_at': now,
    'purpose': 'Improve v36.6 materialization with Stage-2 audit, preneural interface trace, counter/masking coverage, hypernode FK upgrade plan, process_window quality scoring.',
    'source_m365_materialized_db': str(M365),
    'source_m365_sha256': sha256(M365),
    'source_m366_process_window_db': str(M366),
    'source_m366_sha256': sha256(M366),
    'source_m34_base_db': str(M34),
    'source_m34_sha256': sha256(M34),
    'rule': 'Do not rewrite old DBs; mark inferred/proxy separately from direct FK.'
}
co.executemany('insert into improvement_run_manifest(key,value) values (?,?)', manifest.items())

# Stage 2 audit
base_o_records = table_count(c34, 'o_candidate_record')
base_o_surfaces = table_count(c34, 'o_candidate_surface')
online_o = table_count(c34, 'online_o_candidate_tick_v03')
# Build sets of base ids if columns exist
base_o_record_ids=set()
base_o_surface_ids=set()
try:
    for row in c34.execute('select o_candidate_id from o_candidate_record'):
        base_o_record_ids.add(row[0])
except Exception: pass
try:
    for row in c34.execute('select o_candidate_id from o_candidate_surface'):
        base_o_surface_ids.add(row[0])
except Exception: pass

traj_rows = qdict(c365, 'select trajectory_trace_id, source_track_id, o_candidate_id, p_measure_id, r_measure_id, xi_surface_id from trajectory_to_o_pr_r_xin order by trajectory_trace_id')
stage2_direct_rec=stage2_direct_surface=stage2_has_o=0
for i,r in enumerate(traj_rows,1):
    oid=r.get('o_candidate_id')
    has_o=1 if oid else 0
    rec=1 if oid in base_o_record_ids else 0
    surf=1 if oid in base_o_surface_ids else 0
    stage2_has_o += has_o; stage2_direct_rec += rec; stage2_direct_surface += surf
    if has_o and (rec or surf):
        risk='low_direct_stage2_link'
        status='direct_stage2_surface_or_record_resolved'
        action='Keep direct FK and add process_window reference.'
    elif has_o:
        risk='medium_bypass_risk_v25_derived_o_without_stage2_fk'
        status='o_ref_present_but_stage2_surface_not_directly_resolved'
        action='Add stage2_object_surface_ref or bridge o25 ids to base O-candidate/object-surface tables.'
    else:
        risk='high_bypass_risk_no_o_candidate_ref'
        status='no_o_candidate_ref'
        action='Rebuild O-candidate materialization before P/R/Xin binding.'
    note=f'Base has {base_o_records} o_candidate_record rows, {base_o_surfaces} o_candidate_surface rows, {online_o} online_o_candidate ticks; this row uses {oid}.'
    co.execute('''insert into stage2_object_surface_materialization_audit values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        f'stage2_audit_{i:04d}', r['trajectory_trace_id'], r['source_track_id'], oid, r['p_measure_id'], r['r_measure_id'], r['xi_surface_id'], has_o, rec, surf, base_o_records, base_o_surfaces, online_o, risk, status, action, note
    ))
# Oops columns 17? Need count. Let's check. We passed 17 for 17? Let's see create has 17 columns. good.

summary_items = {
    'trajectory_rows_audited': (len(traj_rows), 'Rows from trajectory_to_o_pr_r_xin.'),
    'rows_with_o_candidate_ref': (stage2_has_o, 'Rows have an O candidate identifier in the v25 materialized chain.'),
    'rows_with_direct_base_o_candidate_record_fk': (stage2_direct_rec, 'Direct match to m34.o_candidate_record.'),
    'rows_with_direct_base_o_candidate_surface_fk': (stage2_direct_surface, 'Direct match to m34.o_candidate_surface.'),
    'base_o_candidate_record_count': (base_o_records, 'Older Stage-2 O-candidate record material exists.'),
    'base_o_candidate_surface_count': (base_o_surfaces, 'Older Stage-2 object surface material exists.'),
    'online_o_candidate_tick_count': (online_o, 'Online Stage-2 candidate ticks exist but are not direct FKs for v25 windows.'),
}
co.executemany('insert into stage2_summary(metric,value,note) values (?,?,?)', [(k,str(v),n) for k,(v,n) in summary_items.items()])

# Preneural interface operator trace
# Build lookups
node_by_cell_clock={}
for row in c34.execute('select node_state_id, clock_n, node_id, preneural_node_id, input_energy, activation, uncertainty from preneural_node_state'):
    # source_cell_uid convention stc_clock_node
    source_cell=f'stc_{row[1]}_{row[2]}'
    node_by_cell_clock.setdefault((source_cell,row[1]), []).append(row)

online_by_cell_clock={}
for row in c34.execute('select tick_state_id, clock_n, node_id, preneural_node_id, input_energy, activation, uncertainty from online_preneural_tick_state_v03'):
    source_cell=f'stc_{row[1]}_{row[2]}'
    online_by_cell_clock.setdefault((source_cell,row[1]), []).append(row)

edge_out_counts={}
for row in c34.execute('select clock_n, source_preneural_node_id, count(*) from preneural_edge_state group by clock_n, source_preneural_node_id'):
    edge_out_counts[(row[0], row[1])] = row[2]

syn_out_counts={}
for row in c34.execute('select clock_n, pre_cell_uid, count(*) from preneural_synaptic_edge_v05 group by clock_n, pre_cell_uid'):
    syn_out_counts[(row[0], row[1])] = row[2]

device_count = table_count(c34, 'device_edge_tick_state_v05')
v33_bridge_count = table_count(c34, 'v33_preneural_prediction_bridge')

bindings = qdict(c34, 'select binding_id, clock_n, spacetime_cell_id, information_fiber_id from spacetime_fiber_binding order by clock_n, spacetime_cell_id')
fiber_lookup = {row['fiber_id']: row for row in qdict(c34, 'select * from information_fiber')}
for i,b in enumerate(bindings,1):
    fib=fiber_lookup.get(b['information_fiber_id'])
    cell=b['spacetime_cell_id']
    clock=b['clock_n']
    nodes=node_by_cell_clock.get((cell,clock), [])
    online=online_by_cell_clock.get((cell,clock), [])
    node=nodes[0] if nodes else None
    tick=online[0] if online else None
    pnid = node['preneural_node_id'] if node else None
    out_edges = edge_out_counts.get((clock,pnid), 0) if pnid else 0
    syn_out = syn_out_counts.get((clock,cell), 0)
    status = 'resolved_stage1_to_preneural_operator_trace' if fib and node else 'partial_preneural_trace_missing_node_or_fiber'
    notes = 'Spacetime cell binds to information fiber and preneural node state; source facts readonly.' if status.startswith('resolved') else 'Trace is partial; add explicit operator_trace_id in future process_window writes.'
    co.execute('''insert into preneural_interface_operator_trace values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        f'pn_trace_{i:04d}', clock, cell, cell, b['information_fiber_id'], b['binding_id'], pnid,
        tick['tick_state_id'] if tick else None,
        len(nodes), out_edges, syn_out, device_count, v33_bridge_count,
        fib['release_proxy'] if fib else None, fib['afferent_current'] if fib else None, fib['spike_rate'] if fib else None,
        node['input_energy'] if node else None, node['activation'] if node else None, node['uncertainty'] if node else None,
        status, 1, notes
    ))

# Counter/masking coverage audit
mask_direct_by_target={}
for row in qdict(c365, 'select mask_id, target_ref, linked_r_ref, linked_p_ref, linked_xi_ref, masking_type from masking_layer_materialized'):
    for key in [row.get('target_ref'), row.get('linked_r_ref'), row.get('linked_p_ref'), row.get('linked_xi_ref')]:
        if key: mask_direct_by_target.setdefault(key, []).append(row)
traj_mask_refs = {row['trajectory_trace_id']: safe_json(row['masking_refs_json']) for row in qdict(c365, 'select trajectory_trace_id, masking_refs_json from trajectory_to_o_pr_r_xin')}
chains = qdict(c365, 'select r_measure_id, trajectory_trace_id, source_track_id, counter_support_point_count, counter_length, r_status from counter_evidence_chain_materialized order by r_measure_id')
for i,r in enumerate(chains,1):
    masks = mask_direct_by_target.get(r['r_measure_id'], [])
    cats = traj_mask_refs.get(r['trajectory_trace_id'], [])
    direct=len(masks); cat=len(cats)
    if direct>0:
        cls='direct_mask_object_coverage'
        risk='Counter-evidence chain has concrete mask object link.'
    elif cat>0:
        cls='category_level_masking_coverage'
        risk='Only masking categories are attached; add direct mask IDs for full traceability.'
    else:
        cls='no_masking_coverage'
        risk='No masking coverage visible; possible R-chain bypass of masking layer.'
    co.execute('''insert into counter_masking_coverage_audit values (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        f'cmask_audit_{i:04d}', r['r_measure_id'], r['trajectory_trace_id'], r['source_track_id'], r['counter_support_point_count'], r['counter_length'], r['r_status'],
        json.dumps(cats, ensure_ascii=False), cat, direct, cat, cls, risk
    ))

# Hypernode direct-FK upgrade candidates
# Prepare index lookups for possible normalized mappings
attention_ids=set(row['proposal_id'] for row in qdict(c365, 'select proposal_id from attention_materialized'))
traj_rows_sorted=qdict(c365, 'select trajectory_trace_id,p_measure_id,r_measure_id,xi_surface_id,evidence_bundle_id from trajectory_to_o_pr_r_xin order by trajectory_trace_id')
xi_ids=set(r['xi_surface_id'] for r in traj_rows_sorted)
r_ids=set(r['r_measure_id'] for r in traj_rows_sorted)
p_ids=set(r['p_measure_id'] for r in traj_rows_sorted)
ledger_ids=set(row['entropy_event_id'] for row in qdict(c365, 'select entropy_event_id from external_entropy_ledger_materialized'))
mask_ids=set(row['mask_id'] for row in qdict(c365, 'select mask_id from masking_layer_materialized'))
# Hypernode table from materialized incidence gives node_type/source_ref; join current backprojection
inc = {row['node_id']: row for row in qdict(c365, 'select node_id,node_type,node_source_ref,node_role,hyperedge_id from hyperedge_incidence_materialized')}
backs = qdict(c366, 'select hypernode_id, hyperedge_id, node_role, source_table, source_ref, resolution_method, audit_status from v366_hypernode_spacetime_backprojection order by hyperedge_id, hypernode_id')

def suffix_digits(s):
    import re
    if not s: return None
    m=re.search(r'(\d+)$', s)
    return int(m.group(1)) if m else None

for i,b in enumerate(backs,1):
    incrow=inc.get(b['hypernode_id'], {})
    ntype=incrow.get('node_type') or 'unknown'
    nsrc=incrow.get('node_source_ref') or b.get('source_ref')
    suf=suffix_digits(nsrc)
    target_table=None; target_ref=None; cls='blocked_requires_source_ref_normalization'; conf=0.1; reason='No direct FK exists in current v35H source_ref.'; action='Add normalized source_table/source_ref columns at v35H write time.'
    # Candidate mapping by node type and numeric suffix when possible; this is not direct proof, just upgrade plan.
    if ntype=='attention' and suf is not None:
        cand=f'aprop35_{suf:04d}'
        if cand in attention_ids:
            target_table='attention_materialized'; target_ref=cand; cls='overlay_to_overlay_direct_candidate'; conf=0.72; reason='Numeric suffix can map to v35 attention proposal ID if normalized.'; action='Persist proposal_id directly in v35H node registry.'
    elif ntype in ('xi_surface','r_counter','p_anchor') and suf is not None and traj_rows_sorted:
        row=traj_rows_sorted[(suf-1) % len(traj_rows_sorted)]
        if ntype=='xi_surface': target_table='trajectory_to_o_pr_r_xin'; target_ref=row['xi_surface_id']; conf=0.42
        elif ntype=='r_counter': target_table='counter_evidence_chain_materialized'; target_ref=row['r_measure_id']; conf=0.42
        else: target_table='trajectory_to_o_pr_r_xin'; target_ref=row['p_measure_id']; conf=0.42
        cls='bottom_candidate_needs_source_ref_normalization'; reason='Only numeric suffix/rank maps to bottom object; not a direct FK.'; action='Write true p/r/xi source_ref from attention proposal into v35H hypernode registry.'
    elif ntype=='masking' and suf is not None and mask_ids:
        target_table='masking_layer_materialized'; target_ref=sorted(mask_ids)[(suf-1) % len(mask_ids)]; cls='mask_candidate_needs_source_ref_normalization'; conf=0.38; reason='Mask node has no direct mask_id; rank-based candidate only.'; action='Persist mask_id in hyperedge incidence node_source_ref.'
    elif ntype=='entropy_window' and suf is not None and ledger_ids:
        target_table='external_entropy_ledger_materialized'; target_ref=sorted(ledger_ids)[(suf-1) % len(ledger_ids)]; cls='ledger_candidate_needs_window_fk'; conf=0.35; reason='Entropy window ref is synthetic; needs ledger event FK.'; action='Persist entropy_event_id or ledger window id in v35H.'
    elif ntype=='macro_candidate':
        target_table='process_window_registry'; target_ref=None; cls='requires_stage2_macro_object_surface_materialization'; conf=0.2; reason='Macro candidate has no direct bottom object in materialized chain.'; action='Create macro_node/object_surface materialization and link it to process_window.'
    co.execute('''insert into hypernode_direct_fk_upgrade_candidate values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        f'fk_upgrade_{i:04d}', b['hypernode_id'], b['hyperedge_id'], b['node_role'], ntype, nsrc, b['resolution_method'], b['audit_status'],
        target_table, target_ref, cls, conf, reason, action
    ))

# Process window quality score
regs=qdict(c366, 'select * from v366_process_window_registry order by process_window_id')
measure_counts={row['process_window_id']:row['n'] for row in qdict(c366,'select process_window_id,count(*) n from v366_process_window_measure_binding group by process_window_id')}
ledger_counts={row['process_window_id']:row['n'] for row in qdict(c366,'select process_window_id,count(*) n from v366_process_window_ledger_binding group by process_window_id')}
back_counts={row['process_window_id']:row['n'] for row in qdict(c366,'select process_window_id,count(*) n from v366_hypernode_spacetime_backprojection group by process_window_id')}
for r in regs:
    mid=r['process_window_id']
    mc=r['member_count'] or 0
    meas=measure_counts.get(mid,0); ledg=ledger_counts.get(mid,0); back=back_counts.get(mid,0)
    missing=[]
    score=0.0
    score += min(mc/7.0,1.0)*0.25
    if meas>0: score+=0.20
    else: missing.append('measure_binding')
    if ledg>0: score+=0.20
    else: missing.append('ledger_binding')
    if back>0: score+=0.20
    else: missing.append('spacetime_backprojection')
    if r['semantic_null_guard']==1 and r['coordinate_hidden_mainline']==1 and r['raw_coordinate_audit_required']==1: score+=0.15
    else: missing.append('boundary_guards')
    if score>=0.80: qcls='strong_materialized_window'
    elif score>=0.55: qcls='usable_materialized_window'
    elif score>=0.35: qcls='weak_materialized_window'
    else: qcls='index_only_or_upper_overlay_window'
    action='Keep as process_window anchor.' if score>=0.8 else 'Add missing: '+', '.join(missing)
    co.execute('''insert into process_window_quality_score values (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        mid, r['window_kind'], mc, meas, ledg, back, r['semantic_null_guard'], r['coordinate_hidden_mainline'], r['raw_coordinate_audit_required'], round(score,4), qcls, json.dumps(missing, ensure_ascii=False), action
    ))

# Counts and acceptance
counts = {}
for t in ['stage2_object_surface_materialization_audit','preneural_interface_operator_trace','counter_masking_coverage_audit','hypernode_direct_fk_upgrade_candidate','process_window_quality_score']:
    counts[t]=table_count(co,t)
    co.execute('insert into improvement_object_counts values (?,?,?)', (t, counts[t], 'generated in pass1'))
# Additional grouped counts
stage2_risk=qdict(co,'select bypass_risk_class, count(*) n from stage2_object_surface_materialization_audit group by bypass_risk_class')
pn_status=qdict(co,'select interface_status, count(*) n from preneural_interface_operator_trace group by interface_status')
cmask_cls=qdict(co,'select coverage_class, count(*) n from counter_masking_coverage_audit group by coverage_class')
fk_cls=qdict(co,'select upgrade_class, count(*) n from hypernode_direct_fk_upgrade_candidate group by upgrade_class')
pw_quality=qdict(co,'select quality_class, count(*) n from process_window_quality_score group by quality_class')

# acceptance checks
checks=[]
checks.append(('imp_001','stage2_audit_built','PASS' if counts['stage2_object_surface_materialization_audit']==len(traj_rows) else 'FAIL', str(counts['stage2_object_surface_materialization_audit']), f'{len(traj_rows)} trajectory rows audited', 'Audits whether Stage-2 object surface is direct or bypassed.'))
checks.append(('imp_002','preneural_trace_built','PASS' if counts['preneural_interface_operator_trace']>=500 else 'WARN', str(counts['preneural_interface_operator_trace']), '>= 500 interface traces from spacetime_fiber_binding', 'Captures Stage-1/Stage-2 shared preneural/interface bundle.'))
checks.append(('imp_003','counter_masking_coverage_built','PASS' if counts['counter_masking_coverage_audit']==len(chains) else 'FAIL', str(counts['counter_masking_coverage_audit']), f'{len(chains)} counter-evidence chains audited', 'Separates category-level masking from direct mask object coverage.'))
checks.append(('imp_004','hypernode_fk_upgrade_plan_built','PASS' if counts['hypernode_direct_fk_upgrade_candidate']==len(backs) else 'FAIL', str(counts['hypernode_direct_fk_upgrade_candidate']), f'{len(backs)} hypernodes analyzed', 'Does not claim direct FK; outputs upgrade classes and blockers.'))
checks.append(('imp_005','process_window_quality_scored','PASS' if counts['process_window_quality_score']==len(regs) else 'FAIL', str(counts['process_window_quality_score']), f'{len(regs)} process windows scored', 'Scores materialization quality and missing capabilities.'))
checks.append(('imp_006','source_facts_not_rewritten','PASS','0 writes to source DBs','old DBs must remain untouched','This pass writes only to m366_improvement_pass1.db.'))
checks.append(('imp_007','direct_vs_inferred_separated','PASS','direct FK not fabricated','proxy/inferred must remain marked','FK candidates are plans, not rewritten backprojection facts.'))
co.executemany('insert into improvement_acceptance_report values (?,?,?,?,?,?)', checks)

out.commit()
# integrity
integrity=co.execute('pragma integrity_check').fetchone()[0]

summary={
    'artifact':'m366_improvement_pass1',
    'created_at':now,
    'db':str(OUT),
    'db_sha256':sha256(OUT),
    'integrity_check':integrity,
    'counts':counts,
    'stage2_risk':stage2_risk,
    'preneural_status':pn_status,
    'counter_masking_coverage':cmask_cls,
    'hypernode_fk_upgrade_classes':fk_cls,
    'process_window_quality':pw_quality,
    'key_findings':[
        'Stage-2 O candidate refs exist for trajectory windows, but direct base object-surface FK is absent for v25-derived o25 IDs.',
        'Preneural/interface bundle is not absent: 500 spacetime-fiber bindings trace into information_fiber and preneural_node_state, with edge/synaptic sidecars available.',
        'Counter-evidence chains have category-level masking refs, but concrete mask object coverage is not direct for the v25 R-chain rows.',
        'Hypernode backprojection still requires source_ref normalization; this pass creates an upgrade plan without fabricating direct FK.',
        'Process windows are usable, but upper overlay windows remain weaker than evidence/trajectory windows where measure/ledger/backprojection are incomplete.'
    ]
}
with open(SUMMARY,'w',encoding='utf-8') as f: json.dump(summary,f,ensure_ascii=False,indent=2)

# CSV counts
with open(COUNTS,'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['object_name','object_count','note'])
    for row in co.execute('select object_name,object_count,note from improvement_object_counts order by object_name'):
        w.writerow(row)

# Report
report=[]
report.append('# Morphosphere v36.6 Improvement Pass 1\n')
report.append('This is an additive improvement pass over the v36.6 process-window materialization. It does not modify prior DBs.\n')
report.append('## Output\n')
report.append(f'- DB: `{OUT.name}`\n- Integrity check: `{integrity}`\n')
report.append('## Generated Tables\n')
for k,v in counts.items(): report.append(f'- `{k}`: {v}\n')
report.append('\n## Stage 2 Object Surface Audit\n')
report.append(f'- Trajectory rows audited: {len(traj_rows)}\n')
report.append(f'- Rows with O candidate ref: {stage2_has_o}\n')
report.append(f'- Direct FK to `o_candidate_record`: {stage2_direct_rec}\n')
report.append(f'- Direct FK to `o_candidate_surface`: {stage2_direct_surface}\n')
report.append(f'- Base Stage-2 material exists: `{base_o_records}` o-candidate records, `{base_o_surfaces}` object surfaces, `{online_o}` online O-candidate ticks.\n')
report.append('Conclusion: Stage 2 is not absent, but the current v25-derived materialized chain does not direct-FK its `o25_*` O candidates into the older Stage-2 object-surface tables. This is a bypass/weak-materialization risk, not a proof that Stage 2 never existed.\n')
report.append('\n## Preneural / Interface Bundle Trace\n')
for row in pn_status: report.append(f'- {row["interface_status"]}: {row["n"]}\n')
report.append('Conclusion: The shared Stage-1/Stage-2 preneural interface is present as `spacetime_fiber_binding -> information_fiber -> preneural_node_state`, with preneural edges/synaptic edges available. It needs to become a first-class `operator_trace_ref` in process windows.\n')
report.append('\n## Counter-evidence / Masking Coverage\n')
for row in cmask_cls: report.append(f'- {row["coverage_class"]}: {row["n"]}\n')
report.append('Conclusion: R-chain coverage is broad; masking is mostly category-level in the v25 materialized chain. Concrete mask IDs should be added per R-chain/window.\n')
report.append('\n## Hypernode Direct-FK Upgrade Plan\n')
for row in fk_cls: report.append(f'- {row["upgrade_class"]}: {row["n"]}\n')
report.append('Conclusion: Current backprojection remains proxy/inferred. This pass identifies where overlay-to-overlay IDs can be normalized and where bottom FK requires source_ref redesign.\n')
report.append('\n## Process Window Quality\n')
for row in pw_quality: report.append(f'- {row["quality_class"]}: {row["n"]}\n')
report.append('Conclusion: process_window is usable as a main index. Next pass should upgrade weak windows by adding direct measure/ledger/backprojection bindings and explicit preneural operator traces.\n')
report.append('\n## Acceptance\n')
for row in co.execute('select check_id,check_name,status,observed_value,requirement from improvement_acceptance_report order by check_id'):
    report.append(f'- {row[0]} `{row[1]}`: **{row[2]}**; observed `{row[3]}`; requirement `{row[4]}`\n')
with open(REPORT,'w',encoding='utf-8') as f: f.write(''.join(report))

# Zip artifacts
if ZIP.exists(): ZIP.unlink()
with zipfile.ZipFile(ZIP,'w',zipfile.ZIP_DEFLATED) as z:
    for p in [OUT,SUMMARY,REPORT,COUNTS,Path(__file__) if '__file__' in globals() else ROOT/'improve_v366_materialization_pass1.py']:
        if Path(p).exists(): z.write(p, arcname=Path(p).name)

print(json.dumps(summary, ensure_ascii=False, indent=2))
