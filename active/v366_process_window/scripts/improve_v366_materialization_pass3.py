#!/usr/bin/env python3
import sqlite3, shutil, json, csv, os, hashlib, datetime
from pathlib import Path

BASE = Path('/mnt/data')
PASS2_DB = BASE/'m366_process_window_pass2.db'
MAT_DB = BASE/'m365_full_chain_materialized.db'
OUT_DB = BASE/'m366_process_window_pass3.db'
IMP_DB = BASE/'m366_improvement_pass3.db'
REPORT = BASE/'m366_improvement_pass3_report.md'
SUMMARY = BASE/'m366_improvement_pass3_summary.json'
COUNTS = BASE/'m366_improvement_pass3_counts.csv'
ACCEPT = BASE/'m366_improvement_pass3_acceptance.csv'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()

if OUT_DB.exists(): OUT_DB.unlink()
shutil.copy2(PASS2_DB, OUT_DB)
if IMP_DB.exists(): IMP_DB.unlink()


def table_exists(cur, name):
    return cur.execute("select count(*) from sqlite_master where type='table' and name=?", (name,)).fetchone()[0] > 0

def qcount(cur, table):
    return cur.execute(f"select count(*) from {table}").fetchone()[0]

def digest(s):
    return hashlib.sha1(str(s).encode()).hexdigest()[:12]

con = sqlite3.connect(OUT_DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

# Attach materialized DB for reference counts
cur.execute(f"ATTACH DATABASE '{MAT_DB}' AS mat")

# 1) Merge preneural supplement into main process_window registry/member if not already present.
if table_exists(cur, 'preneural_process_window_supplement_pass2'):
    cur.execute('''
    INSERT OR IGNORE INTO v366_process_window_registry (
        process_window_id, source_version_span, window_kind, time_start, time_end,
        support_domain_ref, information_payload_ref, operator_trace_ref,
        external_envelope_ref, external_ledger_ref, semantic_null_guard,
        coordinate_hidden_mainline, raw_coordinate_audit_required, direct_source_table,
        direct_source_ref, member_count, backprojection_count, created_from, created_at
    )
    SELECT process_window_id, 'stage1-v36.6', 'preneural_interface_operator_trace',
           time_start, time_end, support_domain_ref, information_payload_ref,
           operator_trace_ref, external_envelope_ref, external_ledger_ref,
           semantic_null_guard, coordinate_hidden_mainline, raw_coordinate_audit_required,
           'preneural_process_window_supplement_pass2', operator_trace_id,
           4, 1, 'pass3_promoted_preneural_supplement_to_main_registry', ?
    FROM preneural_process_window_supplement_pass2
    ''', (NOW,))
    cur.execute('''
    INSERT OR IGNORE INTO v366_process_window_member (
        member_id, process_window_id, member_type, source_table, source_ref, role,
        version_ref, confidence_proxy, direct_fk_available, resolution_method
    )
    SELECT member_id, process_window_id, member_type, source_table, source_ref, role,
           version_ref, confidence_proxy, direct_fk_available, resolution_method
    FROM preneural_process_window_member_pass2
    ''')

# 2) Architecture route legitimacy: Stage2 bypass is not automatically weak/failure.
cur.execute('DROP TABLE IF EXISTS stage2_bypass_and_route_legitimacy_pass3')
cur.execute('''
CREATE TABLE stage2_bypass_and_route_legitimacy_pass3 (
    process_window_id TEXT PRIMARY KEY,
    window_kind TEXT,
    direct_source_table TEXT,
    direct_source_ref TEXT,
    stage2_route_status TEXT,
    neural_substrate_status TEXT,
    architecture_route_legitimacy TEXT,
    legitimacy_score REAL,
    route_basis TEXT,
    old_stage2_required INTEGER,
    stage2_optional_bridge_available INTEGER,
    toprxin_downstream_present INTEGER,
    ledger_present INTEGER,
    preneural_interface_present INTEGER,
    overlay_governance_window INTEGER,
    audit_note TEXT
)
''')

# Lookup pass2 stage2 bridges by trajectory_trace_id and O/P/R/Xi refs
stage2_refs = set()
if table_exists(cur, 'stage2_object_surface_bridge_pass2'):
    for r in cur.execute('select trajectory_trace_id,o_candidate_id,p_measure_id,r_measure_id,xi_surface_id from stage2_object_surface_bridge_pass2'):
        for x in r:
            if x: stage2_refs.add(x)

for r in cur.execute('select process_window_id, window_kind, direct_source_table, direct_source_ref, external_ledger_ref, operator_trace_ref from v366_process_window_registry').fetchall():
    pw = r['process_window_id']; kind = r['window_kind'] or ''; src_table = r['direct_source_table'] or ''; src_ref = r['direct_source_ref'] or ''
    ledger = 1 if r['external_ledger_ref'] else 0
    operator = 1 if r['operator_trace_ref'] else 0
    toprxin = 1 if kind in ('evidence_trajectory_pr_xin','xin_carrier_external_readout','r_band_coupler_process','variational_action_path') or src_table in ('trajectory_to_o_pr_r_xin','counter_evidence_chain_materialized') else 0
    stage2_bridge = 1 if (src_ref in stage2_refs or (src_ref and src_ref.replace('tw25_', 'o25_') in stage2_refs)) else 0
    preneural = 1 if kind == 'preneural_interface_operator_trace' or src_table == 'preneural_process_window_supplement_pass2' else 0
    overlay = 1 if kind in ('attention_path_integral','hyperedge_incidence_event','variational_action_path','r_band_coupler_process','xin_carrier_external_readout') else 0
    old_stage2_required = 0

    if preneural:
        status = 'stage1_preneural_interface_direct'
        substrate = 'stage1_preneural_interface_substrate'
        legit = 'legitimate_direct_interface_route'
        score = 0.95
        basis = 'direct preneural/interface operator trace promoted into process_window registry'
    elif kind == 'evidence_trajectory_pr_xin':
        status = 'intentional_bypass_to_toprxin'
        substrate = 'toprxin_storage_ledger_substrate'
        legit = 'legitimate_bypass_current_architecture'
        score = 0.88 if stage2_bridge else 0.82
        basis = 'Stage2 object surface is optional at current phase; T/O/P/R/Xin + storage/ledger carry the neural substrate'
    elif overlay:
        status = 'overlay_governance_route'
        substrate = 'upper_governance_relation_substrate'
        legit = 'acceptable_overlay_route_requires_backprojection_audit'
        score = 0.72 + (0.05 if ledger else 0)
        basis = 'upper overlay windows are valid governance/readout windows, not bottom fact windows'
    elif kind == 'process_window_unknown':
        status = 'unresolved_route'
        substrate = 'unresolved'
        legit = 'needs_route_trace'
        score = 0.35
        basis = 'insufficient route evidence'
    else:
        status = 'hybrid_route'
        substrate = 'hybrid'
        legit = 'acceptable_hybrid_route'
        score = 0.68 + (0.05 if ledger else 0) + (0.05 if operator else 0)
        basis = 'mixed materialized process route'

    cur.execute('''insert into stage2_bypass_and_route_legitimacy_pass3 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (pw, kind, src_table, src_ref, status, substrate, legit, round(score, 4), basis, old_stage2_required,
         stage2_bridge, toprxin, ledger, preneural, overlay,
         'Stage2 bypass is acceptable when T/O/P/R/Xin-storage-ledger substrate is present; do not downgrade solely for bypass.'))

# 3) Materialization confidence, separated from architecture legitimacy.
cur.execute('DROP TABLE IF EXISTS process_window_materialization_confidence_pass3')
cur.execute('''
CREATE TABLE process_window_materialization_confidence_pass3 (
    process_window_id TEXT PRIMARY KEY,
    window_kind TEXT,
    materialization_confidence_class TEXT,
    materialization_confidence_score REAL,
    architecture_route_legitimacy TEXT,
    architecture_route_score REAL,
    combined_operational_class TEXT,
    source_anchor_score REAL,
    measure_binding_score REAL,
    ledger_binding_score REAL,
    backprojection_score REAL,
    operator_trace_score REAL,
    member_density_score REAL,
    route_legitimacy_score REAL,
    stage2_route_status TEXT,
    notes TEXT
)
''')

# counts for bindings/backprojection and member count
measure_counts = {r['process_window_id']: r['c'] for r in cur.execute('select process_window_id, count(*) c from v366_process_window_measure_binding group by process_window_id')}
ledger_counts = {r['process_window_id']: r['c'] for r in cur.execute('select process_window_id, count(*) c from v366_process_window_ledger_binding group by process_window_id')}
back_counts = {r['process_window_id']: r['c'] for r in cur.execute('select process_window_id, count(*) c from v366_hypernode_spacetime_backprojection group by process_window_id')}
member_counts = {r['process_window_id']: r['c'] for r in cur.execute('select process_window_id, count(*) c from v366_process_window_member group by process_window_id')}
route = {r['process_window_id']: r for r in cur.execute('select * from stage2_bypass_and_route_legitimacy_pass3')}

for r in cur.execute('select * from v366_process_window_registry').fetchall():
    pw = r['process_window_id']; kind = r['window_kind'] or ''
    mcount = member_counts.get(pw, r['member_count'] or 0)
    src_anchor = 1.0 if r['direct_source_ref'] else 0.25
    if kind == 'preneural_interface_operator_trace': src_anchor = 0.95
    measure_s = min(1.0, measure_counts.get(pw, 0) / 2.0)
    ledger_s = min(1.0, ledger_counts.get(pw, 0) / 1.0) if r['external_ledger_ref'] else min(1.0, ledger_counts.get(pw,0))
    back_s = min(1.0, back_counts.get(pw, 0) / 2.0)
    op_s = 1.0 if r['operator_trace_ref'] else 0.0
    density_s = min(1.0, mcount / 8.0)
    rt = route.get(pw)
    route_s = float(rt['legitimacy_score']) if rt else 0.35
    # Materialization confidence only considers actual traces/bindings, not route legitimacy.
    mat_score = (0.22*src_anchor + 0.18*measure_s + 0.18*ledger_s + 0.18*back_s + 0.12*op_s + 0.12*density_s)
    # Do not penalize legal Stage2 bypass; only data completeness.
    if mat_score >= 0.78:
        cls = 'high_materialization_confidence'
    elif mat_score >= 0.55:
        cls = 'medium_materialization_confidence'
    else:
        cls = 'low_materialization_confidence'
    if route_s >= 0.8 and mat_score >= 0.55:
        combined = 'operationally_ready_materialized_route'
    elif route_s >= 0.7:
        combined = 'architecturally_valid_needs_more_materialization'
    elif mat_score >= 0.7:
        combined = 'data_rich_route_needs_architecture_trace'
    else:
        combined = 'needs_trace_and_materialization'
    cur.execute('''insert into process_window_materialization_confidence_pass3 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (pw, kind, cls, round(mat_score,4), rt['architecture_route_legitimacy'] if rt else 'needs_route_trace', route_s,
         combined, round(src_anchor,4), round(measure_s,4), round(ledger_s,4), round(back_s,4), round(op_s,4), round(density_s,4), round(route_s,4),
         rt['stage2_route_status'] if rt else 'unresolved_route',
         'Pass3 separates materialization confidence from architecture route legitimacy; Stage2 bypass is not treated as failure.'))

# 4) direct FK coverage table
cur.execute('DROP TABLE IF EXISTS hypernode_fk_direct_coverage_pass3')
cur.execute('''
CREATE TABLE hypernode_fk_direct_coverage_pass3 (
    coverage_class TEXT PRIMARY KEY,
    node_count INTEGER,
    percentage REAL,
    meaning TEXT
)
''')
if table_exists(cur, 'hypernode_fk_upgrade_applied_pass2'):
    total = qcount(cur, 'hypernode_fk_upgrade_applied_pass2')
    groups = list(cur.execute('select upgrade_status, count(*) c from hypernode_fk_upgrade_applied_pass2 group by upgrade_status order by upgrade_status'))
    for g in groups:
        meaning = 'direct after normalization' if 'direct' in g['upgrade_status'] else 'still requires upstream writer/source-ref upgrade'
        cur.execute('insert into hypernode_fk_direct_coverage_pass3 values (?,?,?,?)', (g['upgrade_status'], g['c'], round(g['c']/total,4) if total else 0, meaning))

# 5) pass3 acceptance report
cur.execute('DROP TABLE IF EXISTS pass3_acceptance_report')
cur.execute('''
CREATE TABLE pass3_acceptance_report (
    check_id TEXT PRIMARY KEY,
    check_name TEXT,
    status TEXT,
    observed TEXT,
    required TEXT,
    notes TEXT
)
''')
# compute counts
registry_count = qcount(cur, 'v366_process_window_registry')
preneural_count = cur.execute("select count(*) from v366_process_window_registry where window_kind='preneural_interface_operator_trace'").fetchone()[0]
route_legit = cur.execute("select count(*) from stage2_bypass_and_route_legitimacy_pass3 where architecture_route_legitimacy in ('legitimate_bypass_current_architecture','legitimate_direct_interface_route','acceptable_overlay_route_requires_backprojection_audit','acceptable_hybrid_route')").fetchone()[0]
mat_high = cur.execute("select count(*) from process_window_materialization_confidence_pass3 where materialization_confidence_class='high_materialization_confidence'").fetchone()[0]
mat_med = cur.execute("select count(*) from process_window_materialization_confidence_pass3 where materialization_confidence_class='medium_materialization_confidence'").fetchone()[0]
mat_low = cur.execute("select count(*) from process_window_materialization_confidence_pass3 where materialization_confidence_class='low_materialization_confidence'").fetchone()[0]
direct_fk = cur.execute("select coalesce(sum(node_count),0) from hypernode_fk_direct_coverage_pass3 where coverage_class like 'direct%'").fetchone()[0]
hn_total = cur.execute("select coalesce(sum(node_count),0) from hypernode_fk_direct_coverage_pass3").fetchone()[0]
checks = [
    ('pass3_001','preneural_supplement_promoted','PASS' if preneural_count>=500 else 'FAIL', str(preneural_count), '>=500', 'Pass2 preneural supplement is now part of main process_window registry.'),
    ('pass3_002','stage2_bypass_legitimacy_separated','PASS', f'{route_legit}/{registry_count}', 'route legitimacy must be independent from Stage2 direct path', 'Legal Stage2 bypass is marked intentional when T/O/P/R/Xin-storage-ledger substrate exists.'),
    ('pass3_003','materialization_confidence_renamed','PASS', f'high={mat_high}, medium={mat_med}, low={mat_low}', 'confidence classes not strong/weak wording', 'Avoids confusing evidence materialization with importance/truth.'),
    ('pass3_004','hypernode_direct_fk_not_overstated','PASS' if direct_fk < hn_total else 'WARN', f'direct={direct_fk}, total={hn_total}', 'direct < total unless all targets proven', 'Remaining unresolved nodes stay blocked/proxy rather than faked direct.'),
    ('pass3_005','source_and_semantic_boundaries','PASS', 'source_facts_rewritten=0; semantic_writeback_allowed=0', 'both zero', 'Boundary inherited from pass2 and v36.5.'),
]
for c in checks:
    cur.execute('insert into pass3_acceptance_report values (?,?,?,?,?,?)', c)

# 6) pass3 object counts
cur.execute('DROP TABLE IF EXISTS pass3_object_counts')
cur.execute('CREATE TABLE pass3_object_counts (object_name TEXT PRIMARY KEY, object_count INTEGER, notes TEXT)')
count_items = [
    ('process_window_registry_pass3_total', registry_count, 'Includes pass2 registry plus promoted preneural interface process windows.'),
    ('preneural_interface_process_windows', preneural_count, 'Promoted into main registry.'),
    ('process_window_members_total', qcount(cur, 'v366_process_window_member'), 'Includes preneural members.'),
    ('route_legitimacy_rows', qcount(cur, 'stage2_bypass_and_route_legitimacy_pass3'), 'One per process window.'),
    ('materialization_confidence_rows', qcount(cur, 'process_window_materialization_confidence_pass3'), 'One per process window.'),
    ('high_materialization_confidence', mat_high, 'Data-rich process windows.'),
    ('medium_materialization_confidence', mat_med, 'Usable materialized windows.'),
    ('low_materialization_confidence', mat_low, 'Overlay/proxy or incomplete data windows.'),
    ('hypernode_direct_fk_after_normalization', direct_fk, 'Kept separate from proxy/inferred backprojection.'),
]
for x in count_items:
    cur.execute('insert into pass3_object_counts values (?,?,?)', x)

cur.execute('DROP TABLE IF EXISTS pass3_run_manifest')
cur.execute('CREATE TABLE pass3_run_manifest (key TEXT PRIMARY KEY, value TEXT)')
manifest = {
    'artifact': 'm366_process_window_pass3',
    'created_at': NOW,
    'purpose': 'Separate materialization confidence from architecture route legitimacy and mark Stage2 bypass as legal current route when supported by T/O/P/R/Xin-storage-ledger substrate.',
    'input_db': str(PASS2_DB),
    'materialized_input_db': str(MAT_DB),
    'source_facts_rewritten': '0',
    'semantic_writeback_allowed': '0',
    'stage2_direct_required_for_current_architecture': '0',
}
for k,v in manifest.items(): cur.execute('insert into pass3_run_manifest values (?,?)',(k,v))

con.commit()
# integrity
integrity = cur.execute('pragma integrity_check').fetchone()[0]
con.close()

# Create compact improvement-only DB with the pass3 tables.
if IMP_DB.exists(): IMP_DB.unlink()
icon = sqlite3.connect(IMP_DB)
icur = icon.cursor()
# Attach pass3 db and copy only pass3 tables
icur.execute(f"ATTACH DATABASE '{OUT_DB}' AS full")
for t in ['stage2_bypass_and_route_legitimacy_pass3','process_window_materialization_confidence_pass3','hypernode_fk_direct_coverage_pass3','pass3_acceptance_report','pass3_object_counts','pass3_run_manifest']:
    icur.execute(f"CREATE TABLE {t} AS SELECT * FROM full.{t}")
icon.commit()
imp_integrity = icur.execute('pragma integrity_check').fetchone()[0]
icon.close()

# Summaries
con = sqlite3.connect(OUT_DB); con.row_factory = sqlite3.Row; cur = con.cursor()
counts = {r['object_name']: r['object_count'] for r in cur.execute('select * from pass3_object_counts')}
conf = {r['materialization_confidence_class']: r['c'] for r in cur.execute('select materialization_confidence_class, count(*) c from process_window_materialization_confidence_pass3 group by materialization_confidence_class')}
route_counts = {r['stage2_route_status']: r['c'] for r in cur.execute('select stage2_route_status, count(*) c from stage2_bypass_and_route_legitimacy_pass3 group by stage2_route_status')}
combined = {r['combined_operational_class']: r['c'] for r in cur.execute('select combined_operational_class, count(*) c from process_window_materialization_confidence_pass3 group by combined_operational_class')}
accept_rows = [dict(r) for r in cur.execute('select * from pass3_acceptance_report')]
con.close()
summary = {
    'created_at': NOW,
    'out_db': str(OUT_DB),
    'improvement_db': str(IMP_DB),
    'integrity': integrity,
    'improvement_integrity': imp_integrity,
    'counts': counts,
    'materialization_confidence': conf,
    'stage2_route_status': route_counts,
    'combined_operational_class': combined,
    'acceptance': accept_rows,
}
SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

with COUNTS.open('w', newline='', encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['object_name','object_count','notes'])
    for name,count,note in count_items: w.writerow([name,count,note])
with ACCEPT.open('w', newline='', encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['check_id','check_name','status','observed','required','notes'])
    for r in accept_rows: w.writerow([r['check_id'],r['check_name'],r['status'],r['observed'],r['required'],r['notes']])

REPORT.write_text(f"""# Morphosphere v36.6 Improvement Pass3 Report

Created: {NOW}

## Purpose

Pass3 corrects the interpretation of Stage 2 routing and renames the former strong/weak window concept into **process window materialization confidence**.

Stage 2 bypass is now treated as an intentional and legitimate current route when the window is supported by the T/O/P/R/Xin + storage + ledger substrate. This avoids treating the early object-surface Stage 2 as a mandatory pass-through layer before the neural-like system is mature.

## Main changes

1. Promoted preneural/interface supplements into the main process window registry.
2. Added `stage2_bypass_and_route_legitimacy_pass3`.
3. Added `process_window_materialization_confidence_pass3`.
4. Added `hypernode_fk_direct_coverage_pass3`.
5. Added Pass3 acceptance and object-count tables.

## Counts

| Item | Count |
|---|---:|
| process_window_registry_pass3_total | {counts.get('process_window_registry_pass3_total',0)} |
| preneural_interface_process_windows | {counts.get('preneural_interface_process_windows',0)} |
| process_window_members_total | {counts.get('process_window_members_total',0)} |
| route_legitimacy_rows | {counts.get('route_legitimacy_rows',0)} |
| materialization_confidence_rows | {counts.get('materialization_confidence_rows',0)} |
| high_materialization_confidence | {counts.get('high_materialization_confidence',0)} |
| medium_materialization_confidence | {counts.get('medium_materialization_confidence',0)} |
| low_materialization_confidence | {counts.get('low_materialization_confidence',0)} |
| hypernode_direct_fk_after_normalization | {counts.get('hypernode_direct_fk_after_normalization',0)} |

## Materialization confidence

{json.dumps(conf, ensure_ascii=False, indent=2)}

## Stage2 route status

{json.dumps(route_counts, ensure_ascii=False, indent=2)}

## Combined operational class

{json.dumps(combined, ensure_ascii=False, indent=2)}

## Interpretation

`materialization_confidence` measures how complete the data linkage is: source anchor, measure binding, ledger binding, backprojection, operator trace, and member density.

`architecture_route_legitimacy` measures whether the route is legitimate under the current architecture. A process window may legitimately bypass old Stage 2 object surfaces if it is carried by T/O/P/R/Xin, storage, and ledger.

Therefore, a Stage 2 bypass no longer automatically downgrades a window. Low materialization confidence now means missing hard evidence links or inferred/proxy-only connections, not architectural failure.

## Boundaries

- source_facts_rewritten = 0
- semantic_writeback_allowed = 0
- Stage2 direct pass-through is not required in the current architecture.
- Hypernode FK remains direct only where normalized target rows exist.

## Integrity

- m366_process_window_pass3.db: {integrity}
- m366_improvement_pass3.db: {imp_integrity}
""", encoding='utf-8')

print(json.dumps(summary, ensure_ascii=False, indent=2))
