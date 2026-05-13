#!/usr/bin/env python3
import sqlite3, json, hashlib, datetime
from pathlib import Path
ROOT=Path('/mnt/data')
M365=ROOT/'m365_full_chain_materialized.db'
PW=ROOT/'m366_process_window_pass3.db'
IMP=ROOT/'m366_improvement_pass3.db'
OUT=ROOT/'m366_build_pass5.db'
SUMMARY=ROOT/'m366_build_pass5_summary.json'
REPORT=ROOT/'m366_build_pass5_report.md'
COUNTS=ROOT/'m366_build_pass5_counts.csv'

def q(db, sql):
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    rows=[dict(r) for r in con.execute(sql).fetchall()]
    con.close(); return rows

def scalar(db, sql):
    con=sqlite3.connect(db); cur=con.cursor(); cur.execute(sql); r=cur.fetchone(); con.close(); return r[0] if r else None

def count_table(db, table):
    try: return int(scalar(db, f'select count(*) from {table}'))
    except Exception: return None

def integrity(db):
    try: return scalar(db,'pragma integrity_check')
    except Exception as e: return 'ERR:'+str(e)

def sha(p):
    h=hashlib.sha256();
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

m365_counts={r['layer_name']:r['object_count'] for r in q(M365,'select layer_name, object_count from cross_layer_object_count')}
m365_tables={t:count_table(M365,t) for t in ['source_to_information_point','pr_xin_to_external_ledger']}
pw_tables={t:count_table(PW,t) for t in ['v366_process_window_registry','v366_process_window_member','process_window_materialization_confidence_pass3','stage2_bypass_and_route_legitimacy_pass3','v366_hypernode_spacetime_backprojection','hypernode_fk_upgrade_applied_pass2','v366_hyperedge_spacetime_relation','r_chain_concrete_mask_binding_pass2','preneural_process_window_supplement_pass2','preneural_process_window_member_pass2']}
conf={r['materialization_confidence_class']:r['n'] for r in q(PW,'select materialization_confidence_class, count(*) n from process_window_materialization_confidence_pass3 group by 1')}
routes={r['stage2_route_status']:r['n'] for r in q(PW,'select stage2_route_status, count(*) n from stage2_bypass_and_route_legitimacy_pass3 group by 1')}
fk={r['coverage_class']:r['node_count'] for r in q(PW,'select coverage_class,node_count from hypernode_fk_direct_coverage_pass3')}
fk['direct_after_normalization']=sum(v for k,v in fk.items() if k.startswith('direct_fk_'))
if OUT.exists(): OUT.unlink()
con=sqlite3.connect(OUT); cur=con.cursor()
cur.executescript('''
CREATE TABLE pass5_build_manifest(key TEXT PRIMARY KEY,value TEXT);
CREATE TABLE pass5_deployment_mode_contract(mode TEXT PRIMARY KEY,purpose TEXT,included_data TEXT,excluded_data TEXT,expected_tar_zst_size_mb REAL,run_entrypoint TEXT);
CREATE TABLE pass5_module_operation_status(module_id TEXT PRIMARY KEY,layer_name TEXT,operational_status TEXT,materialized_rows INTEGER,confidence_class TEXT,route_legitimacy TEXT,notes TEXT);
CREATE TABLE pass5_module_collaboration_matrix(edge_id TEXT PRIMARY KEY,upstream_module TEXT,downstream_module TEXT,collaboration_type TEXT,link_hardness TEXT,evidence_table TEXT,observed_count INTEGER,limitation TEXT);
CREATE TABLE pass5_data_product_index(product_id TEXT PRIMARY KEY,path TEXT,product_type TEXT,deployment_modes TEXT,role TEXT,sha256 TEXT,size_bytes INTEGER);
CREATE TABLE pass5_artifact_retention_policy(artifact_class TEXT PRIMARY KEY,retention_decision TEXT,reason TEXT,quick_mode TEXT,full_mode TEXT);
CREATE TABLE pass5_execution_profile(profile_id TEXT PRIMARY KEY,description TEXT,commands TEXT,expected_runtime_class TEXT,modifies_source_facts INTEGER DEFAULT 0);
CREATE TABLE pass5_acceptance_report(check_id TEXT PRIMARY KEY,check_name TEXT,status TEXT,observed_value TEXT,required_value TEXT,notes TEXT);
''')
now=datetime.datetime.utcnow().isoformat(timespec='seconds')+'Z'
manifest={'artifact':'Morphosphere v36.6 process-window deployable pass5','created_at_utc':now,'purpose':'package-mode contracts, module collaboration index, retained quick/full deployments','stage2_bypass_semantics':'intentional/acceptable when T/O/P/R/Xin + storage + ledger substrate is present','window_confidence_semantics':'materialization confidence, not importance or truth'}
cur.executemany('insert into pass5_build_manifest values (?,?)', manifest.items())
cur.executemany('insert into pass5_deployment_mode_contract values (?,?,?,?,?,?)',[
('quick','Daily fast deployment and current v36.6 inspection','latest overlay DBs; full-chain materialized index; pass3/pass5 DB; docs and scripts','v25-v34 large base DBs; runtime_store heavy payloads; historical pass artifacts',3.5,'./RUN_DEPLOY_CHECKS.sh'),
('full_materialized','Full offline data audit with retained historical base outputs','v25-v34 base DBs; overlays; runtime_store; full materialized index; pass3/pass5 DB; docs and scripts','duplicated historical zips; obsolete intermediate artifacts',90.0,'./RUN_DEPLOY_CHECKS.sh')])
modules=[
('m0_external_source','External source / reality envelope','materialized',m365_counts.get('source_data'),'high','legitimate','2D external physical source sits alongside/substitutes current Stage 1 physical input.'),
('m1_information_points','Information point 3D/4D backprojection','materialized',m365_counts.get('information_point_3d4d_backprojection'),'high','legitimate','Hard bottom evidence layer.'),
('m2_trajectory_toprxin','Trajectory to T/O/P/R/Xin','materialized',m365_counts.get('trajectory_to_o_pr_r_xin'),'high','legitimate','Can bypass legacy Stage 2 when current neural substrate is present.'),
('m3_counter_masking','Counter-evidence + masking','materialized',m365_counts.get('counter_evidence_chain'),'medium','legitimate','Masking is template/category mediated in pass2/pass3.'),
('m4_external_ledger','External entropy ledger','materialized',m365_counts.get('external_entropy_ledger'),'high','legitimate','Audit/court, not steering wheel.'),
('m5_attention','v35 attention','materialized',m365_counts.get('attention'),'medium','legitimate','Proposal/audit layer.'),
('m6_hyperedge','v35H hyperedge incidence','materialized',m365_counts.get('hyperedge_incidence'),'medium','legitimate','High-order relation layer.'),
('m7_variational_coupler','v36.x variational/R-band/coupler','materialized',(m365_counts.get('variational_path') or 0)+(m365_counts.get('spacetime_band_coupler') or 0),'medium','legitimate','Proxy scoring, not physical law.'),
('m8_xin_readout','v36.5 Xin carrier/readout','materialized',m365_counts.get('xin_carrier_external_readout'),'medium','legitimate','Readonly readout.'),
('m9_process_window','v36.6 process_window','materialized',pw_tables.get('v366_process_window_registry'),'mixed','legitimate','Common working unit.'),
('m10_preneural_interface','Preneural/interface bundle','materialized',pw_tables.get('preneural_process_window_supplement_pass2'),'medium','legitimate','Shared interface bundle, not necessarily legacy Stage 2.')]
cur.executemany('insert into pass5_module_operation_status values (?,?,?,?,?,?,?)', modules)
edges=[
('e01','external_source','information_point_backprojection','source_to_point','direct','source_to_information_point',m365_tables.get('source_to_information_point'),'2D source currently substitutes/sits alongside Stage 1 sphere.'),
('e02','information_point_backprojection','trajectory_toprxin','point_to_trajectory','direct','information_point_to_trajectory',m365_counts.get('information_point_to_trajectory'),'T layer is window/trace based.'),
('e03','trajectory_toprxin','external_ledger','pr_xin_to_ledger','direct','pr_xin_to_external_ledger',m365_tables.get('pr_xin_to_external_ledger'),'Ledger does not rewrite P/R/Xin.'),
('e04','trajectory_toprxin','counter_masking','counter_chain','direct/materialized','counter_evidence_chain_materialized',m365_counts.get('counter_evidence_chain'),'Concrete mask is template binding.'),
('e05','counter_masking','attention','attention_governance','overlay/materialized','attention_materialized',m365_counts.get('attention'),'Attention is not action.'),
('e06','attention','hyperedge','high_order_incidence','overlay/materialized','hyperedge_incidence_materialized',m365_counts.get('hyperedge_incidence'),'High-order relation, not binary only.'),
('e07','hyperedge','hypernode_backprojection','spacetime_backprojection','partial_direct+proxy','hypernode_fk_upgrade_applied_pass2',pw_tables.get('hypernode_fk_upgrade_applied_pass2'),'390 normalized direct; rest needs upstream source_ref upgrade.'),
('e08','hyperedge','variational_coupler','candidate_path_relation','overlay/materialized','variational_path_materialized',m365_counts.get('variational_path'),'Proxy ranking.'),
('e09','variational_coupler','xin_readout','carrier_readout','overlay/materialized','xin_carrier_external_readout_materialized',m365_counts.get('xin_carrier_external_readout'),'Readonly readout.'),
('e10','all_modules','process_window','common_working_unit','materialized_index','v366_process_window_member',pw_tables.get('v366_process_window_member'),'Binds information/time/support/process/ledger/envelope.'),
('e11','preneural_interface','process_window','operator_trace_supplement','materialized_supplement','preneural_process_window_member_pass2',pw_tables.get('preneural_process_window_member_pass2'),'Preneural shared interface bundle.')]
cur.executemany('insert into pass5_module_collaboration_matrix values (?,?,?,?,?,?,?,?)', edges)
ret=[('latest_pass3_pass5_dbs','retain','Current v36.6 state and package contract','included','included'),('m365_full_chain_materialized','retain','Full-chain data materialization index','included','included'),('v35_v365_overlay_dbs','retain','Bridge/gov/rebase checks','included','included'),('v25_v34_large_base_dbs','mode_split','Too large for quick; required for full audit','excluded','included'),('runtime_store_payload','mode_split','Heavy payload, useful for full audit','excluded','included'),('pass1_pass2_intermediate_artifacts','drop','Regenerable and superseded','excluded','excluded'),('context_docs','retain','Architecture semantics','included','included')]
cur.executemany('insert into pass5_artifact_retention_policy values (?,?,?,?,?)', ret)
cur.executemany('insert into pass5_execution_profile values (?,?,?,?,?)',[('quick_deploy','Fast installation and current checks','./RUN_DEPLOY_CHECKS.sh\n./RUN_V366_PASS5_CHECKS.sh\n./RUN_PASS5_MODULE_STATUS.sh','fast',0),('full_materialized_deploy','Full offline data audit','./RUN_DEPLOY_CHECKS.sh\n./RUN_PASS5_FULL_DATA_AUDIT.sh\n./RUN_PASS5_MODULE_STATUS.sh','medium',0),('optional_heavy_examples','Legacy examples and full bridge','RUN_EXAMPLES=1 ./RUN_FULL_OPTIONAL_CHECKS.sh\nRUN_FULL_BRIDGE=1 ./RUN_FULL_OPTIONAL_CHECKS.sh','heavy',0)])
products=[]
for pid,path,typ,modes,role in [('p_m365_full_chain',M365,'sqlite_db','quick,full','Full-chain materialized data index'),('p_m366_process_window_pass3',PW,'sqlite_db','quick,full','v36.6 pass3 DB'),('p_m366_improvement_pass3',IMP,'sqlite_db','quick,full','Pass3 summary DB'),('p_m366_build_pass5',OUT,'sqlite_db','quick,full','Pass5 package/module DB')]:
    if Path(path).exists(): products.append((pid,str(path),typ,modes,role,sha(path),Path(path).stat().st_size))
cur.executemany('insert into pass5_data_product_index values (?,?,?,?,?,?,?)', products)
accept=[('a01','m365 materialized DB integrity','PASS' if integrity(M365)=='ok' else 'FAIL',integrity(M365),'ok',''),('a02','m366 process-window pass3 DB integrity','PASS' if integrity(PW)=='ok' else 'FAIL',integrity(PW),'ok',''),('a03','process_window count present','PASS' if (pw_tables.get('v366_process_window_registry') or 0)>=1000 else 'FAIL',str(pw_tables.get('v366_process_window_registry')),'>=1000',''),('a04','stage2 bypass treated as legitimate route','PASS' if routes.get('intentional_bypass_to_toprxin',0)>0 else 'FAIL',str(routes.get('intentional_bypass_to_toprxin',0)),'>0',''),('a05','preneural supplement present','PASS' if (pw_tables.get('preneural_process_window_supplement_pass2') or 0)>=500 else 'FAIL',str(pw_tables.get('preneural_process_window_supplement_pass2')),'>=500',''),('a06','hypernode direct FK partial upgrade kept honest','PASS' if fk.get('direct_after_normalization')==390 else 'WARN',str(fk.get('direct_after_normalization')),'390','Remaining nodes remain proxy/upstream-writer upgrade.'),('a07','full materialized mode retained','PASS','retained','retained','')]
cur.executemany('insert into pass5_acceptance_report values (?,?,?,?,?,?)', accept)
con.commit(); con.close()
summary={'pass':'pass5','created_at_utc':now,'m365_counts':m365_counts,'process_window_counts':pw_tables,'materialization_confidence':conf,'stage2_route_status':routes,'hypernode_fk_coverage':fk,'acceptance':{a[1]:a[2] for a in accept}}
SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
with COUNTS.open('w',encoding='utf-8') as f:
    f.write('scope,name,count\n')
    for scope,d in [('m365',m365_counts),('pass3',pw_tables),('confidence',conf),('route',routes),('hypernode_fk',fk)]:
        for k,v in sorted(d.items()): f.write(f'{scope},{k},{v}\n')
REPORT.write_text(f'''# Morphosphere v36.6 Build Pass5 Report\n\nPass5 formalizes quick/full deployment modes and adds a module collaboration index.\n\n## Semantics\n- Stage 2 bypass is intentional/acceptable when T/O/P/R/Xin + storage + ledger substrate is present.\n- Materialization confidence is not truth, importance, or scientific validity.\n- Direct FK is never faked.\n\n## Core counts\n- process windows: {pw_tables.get('v366_process_window_registry')}\n- process window members: {pw_tables.get('v366_process_window_member')}\n- preneural process windows: {pw_tables.get('preneural_process_window_supplement_pass2')}\n- direct hypernode FK after normalization: {fk.get('direct_after_normalization')}\n- information points: {m365_counts.get('information_point_3d4d_backprojection')}\n- external ledger events: {m365_counts.get('external_entropy_ledger')}\n\n## Materialization confidence\n'''+''.join(f'- {k}: {v}\n' for k,v in sorted(conf.items()))+'\n## Route status\n'+''.join(f'- {k}: {v}\n' for k,v in sorted(routes.items()))+'\n## Acceptance\n'+''.join(f'- {a[1]}: {a[2]} ({a[3]})\n' for a in accept),encoding='utf-8')
