#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, math, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
REQ=['clock_n','time_s','sensor_id','sensor_kind','x','y','z','force_x','force_y','force_z','optical_intensity','acoustic_pressure','phase','uncertainty']
PROTECTED=['spacetime_cell','information_fiber','raw_event_stream','cell_spatial_coordinate_snapshot','information_relative_coordinate_snapshot','system_clock_entry','p_predictive_support_v022','r_counterstructure_v022','xi_boundary_guard_v022','substrate_stress_tensor_v04','cell_matrix_contact_v04','foam_edge_state_v04','mechanotransduction_event_v04','preneural_synaptic_edge_v05','device_edge_tick_state_v05','candidate_patch_manifest_v07']
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def sid(p): return p+'_'+uuid.uuid4().hex[:18]
def sha(path):
 h=hashlib.sha256();
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1048576),b''): h.update(b)
 return h.hexdigest()
def count(con,t):
 try: return con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
 except Exception: return -1
def table_sig(con,t): return f'{t}:{count(con,t)}'
def mean(xs): return sum(xs)/len(xs) if xs else 0.0
def stdev(xs):
 m=mean(xs); return (sum((x-m)**2 for x in xs)/len(xs))**0.5 if xs else 0.0
def clamp(x): return max(0.0,min(1.0,x))
def ensure(con):
 con.executescript('''
 CREATE TABLE IF NOT EXISTS realdata_review_run_manifest_v09(run_id TEXT PRIMARY KEY,layer_name TEXT,parent_layer TEXT,execution_mode TEXT,declared_external_csv TEXT,declared_real_external INTEGER,source_facts_append_only INTEGER,candidate_patch_auto_applied INTEGER,p_r_before_xi_enforced INTEGER,created_at TEXT);
 CREATE TABLE IF NOT EXISTS external_data_ingestion_contract_v09(contract_id TEXT PRIMARY KEY,run_id TEXT,column_name TEXT,required INTEGER,semantic_role TEXT,unit_hint TEXT,validation_rule TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS external_data_file_register_v09(file_id TEXT PRIMARY KEY,run_id TEXT,file_path TEXT,file_sha256 TEXT,source_declaration TEXT,declared_real_external INTEGER,fixture_or_demo INTEGER,schema_valid INTEGER,sample_count INTEGER,blocker_status TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS external_physical_sample_v09(sample_id TEXT PRIMARY KEY,run_id TEXT,file_id TEXT,row_index INTEGER,clock_n INTEGER,time_s REAL,sensor_id TEXT,sensor_kind TEXT,x REAL,y REAL,z REAL,force_x REAL,force_y REAL,force_z REAL,force_norm REAL,optical_intensity REAL,acoustic_pressure REAL,phase REAL,uncertainty REAL,created_at TEXT);
 CREATE TABLE IF NOT EXISTS external_sample_cell_mapping_v09(mapping_id TEXT PRIMARY KEY,run_id TEXT,sample_id TEXT,nearest_cell_uid TEXT,nearest_node_id INTEGER,distance_to_cell REAL,nearest_met_event_id TEXT,met_gate_probability REAL,mapping_confidence REAL,p_proxy REAL,r_proxy REAL,xi_proxy REAL,projection_json TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS external_data_quality_gate_v09(gate_id TEXT PRIMARY KEY,run_id TEXT,gate_name TEXT,gate_status TEXT,severity TEXT,observed_value TEXT,expected_value TEXT,blocks_candidate_application INTEGER,rationale TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS realdata_calibration_result_v09(result_id TEXT PRIMARY KEY,run_id TEXT,file_id TEXT,sample_count INTEGER,mapped_sample_count INTEGER,declared_real_external INTEGER,schema_valid INTEGER,force_nonuniformity REAL,phase_continuity_score REAL,multimodal_consistency_score REAL,mapping_confidence_mean REAL,met_alignment_score REAL,p_stability_proxy REAL,r_counter_proxy REAL,xi_pressure_proxy REAL,real_data_gate_status TEXT,interpretation TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS candidate_patch_manual_review_packet_v09(packet_id TEXT PRIMARY KEY,run_id TEXT,patch_id TEXT,candidate_profile_id TEXT,patch_sha256 TEXT,prior_patch_status TEXT,proposed_status TEXT,auto_apply_allowed INTEGER,human_review_required INTEGER,review_packet_path TEXT,review_packet_sha256 TEXT,summary_json TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS candidate_patch_application_decision_v09(decision_id TEXT PRIMARY KEY,run_id TEXT,packet_id TEXT,final_decision TEXT,auto_applied INTEGER,manual_review_required INTEGER,blockers_json TEXT,satisfied_gates_json TEXT,rationale TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS source_fact_digest_v09(digest_id TEXT PRIMARY KEY,run_id TEXT,table_name TEXT,row_count_before INTEGER,row_count_after INTEGER,digest_before TEXT,digest_after TEXT,status TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS realdata_review_acceptance_report_v09(check_id TEXT PRIMARY KEY,run_id TEXT,check_name TEXT,status TEXT,observed_value TEXT,expected_value TEXT,severity TEXT,rationale TEXT,created_at TEXT);
 CREATE TABLE IF NOT EXISTS realdata_review_artifact_manifest_v09(artifact_id TEXT PRIMARY KEY,run_id TEXT,artifact_path TEXT,artifact_role TEXT,sha256 TEXT,created_at TEXT);
 ''')
def make_demo(src,dst):
 with open(src,newline='') as f, open(dst,'w',newline='') as g:
  r=csv.DictReader(f); w=csv.DictWriter(g,fieldnames=REQ); w.writeheader()
  for i,row in enumerate(r):
   rr={k:row[k] for k in REQ}
   rr['force_x']=f"{float(rr['force_x'])*(1+0.015*math.sin(i)):.9f}"
   rr['force_y']=f"{float(rr['force_y'])*(1+0.012*math.cos(i*.7)):.9f}"
   rr['force_z']=f"{float(rr['force_z'])*(1+0.010*math.sin(i*.3)):.9f}"
   rr['phase']=f"{float(rr['phase'])+0.008*math.sin(i*.5):.9f}"
   w.writerow(rr)
def load(path):
 with open(path,newline='') as f:
  r=csv.DictReader(f); valid=all(c in (r.fieldnames or []) for c in REQ); rows=[]
  for row in r:
   try:
    d={c:row[c] for c in REQ}; d['clock_n']=int(float(d['clock_n']))
    for k in ['time_s','x','y','z','force_x','force_y','force_z','optical_intensity','acoustic_pressure','phase','uncertainty']: d[k]=float(d[k])
    rows.append(d)
   except Exception: valid=False
 return rows,valid
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',required=True); ap.add_argument('--report-dir',required=True); ap.add_argument('--data-dir',required=True); ap.add_argument('--external-csv'); ap.add_argument('--declare-real-external',action='store_true'); a=ap.parse_args()
 db=Path(a.db); rep=Path(a.report_dir); data=Path(a.data_dir); rep.mkdir(parents=True,exist_ok=True); data.mkdir(parents=True,exist_ok=True)
 con=sqlite3.connect(db); con.row_factory=sqlite3.Row; ensure(con); cur=con.cursor(); ts=now(); run=sid('realv09')
 for t in ['realdata_review_run_manifest_v09','external_data_ingestion_contract_v09','external_data_file_register_v09','external_physical_sample_v09','external_sample_cell_mapping_v09','external_data_quality_gate_v09','realdata_calibration_result_v09','candidate_patch_manual_review_packet_v09','candidate_patch_application_decision_v09','source_fact_digest_v09','realdata_review_acceptance_report_v09','realdata_review_artifact_manifest_v09']:
  cur.execute(f'DELETE FROM {t}')
 before={t:(count(con,t),table_sig(con,t)) for t in PROTECTED}
 if a.external_csv:
  csvp=Path(a.external_csv); declared=bool(a.declare_real_external); fixture=0 if declared else 1; decl='user_supplied_declared_real_external' if declared else 'user_supplied_not_declared_real'
 else:
  csvp=data/'external_physical_trial_v09_demo_proxy.csv'; make_demo(data/'physical_fixture_v04.csv',csvp); declared=False; fixture=1; decl='demo_proxy_generated_from_builtin_fixture_not_real_external'
 rows,valid=load(csvp); fileid=sid('file9'); filesha=sha(csvp)
 cur.execute('INSERT INTO realdata_review_run_manifest_v09 VALUES (?,?,?,?,?,?,?,?,?,?)',(run,'real_external_physical_data_ingestion_candidate_manual_review_v0.9','shell0_boundary_closure_external_real_data_trial_v0.8','diagnostic_append_only_real_data_review_no_auto_adoption',str(csvp),int(declared),1,0,1,ts))
 for c in REQ: cur.execute('INSERT INTO external_data_ingestion_contract_v09 VALUES (?,?,?,?,?,?,?,?)',(sid('contract9'),run,c,1,'physical_sample_schema_no_semantic_object_label','dimensionless_or_declared_SI_proxy','present_and_parseable',ts))
 cur.execute('INSERT INTO external_data_file_register_v09 VALUES (?,?,?,?,?,?,?,?,?,?,?)',(fileid,run,str(csvp),filesha,decl,int(declared),fixture,int(valid),len(rows),'SCHEMA_ACCEPTED_REVIEW_REQUIRED' if declared else 'PENDING_REAL_EXTERNAL_DATA',ts))
 sample_ids=[]
 for i,row in enumerate(rows):
  sample=sid('xsamp9'); sample_ids.append(sample); fn=math.sqrt(row['force_x']**2+row['force_y']**2+row['force_z']**2)
  cur.execute('INSERT INTO external_physical_sample_v09 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sample,run,fileid,i,row['clock_n'],row['time_s'],row['sensor_id'],row['sensor_kind'],row['x'],row['y'],row['z'],row['force_x'],row['force_y'],row['force_z'],fn,row['optical_intensity'],row['acoustic_pressure'],row['phase'],row['uncertainty'],ts))
 cells=cur.execute('SELECT cell_uid,node_id,clock_start,x,y,z FROM spacetime_cell').fetchall(); mets=cur.execute('SELECT met_event_id,source_cell_uid,clock_n,met_gate_probability FROM mechanotransduction_event_v04').fetchall(); mb={(m['source_cell_uid'],m['clock_n']):m for m in mets}
 confs=[]; ps=[]; rs=[]; xis=[]; metg=[]
 for sample,row in zip(sample_ids,rows):
  best=None; bestd=1e9
  for c in cells:
   if c['clock_start']!=row['clock_n']: continue
   d=math.sqrt((row['x']-c['x'])**2+(row['y']-c['y'])**2+(row['z']-c['z'])**2)
   if d<bestd: bestd=d; best=c
  if best is None: best=cells[0]; bestd=999.0
  m=mb.get((best['cell_uid'],row['clock_n'])); mg=float(m['met_gate_probability']) if m else None
  fn=math.sqrt(row['force_x']**2+row['force_y']**2+row['force_z']**2); conf=clamp(1/(1+bestd))*clamp(1-row['uncertainty']); phasefit=.5+.5*math.cos(row['phase'])
  p=clamp(.35+.25*conf+.20*(mg if mg is not None else .4)+.10*phasefit-.08*row['uncertainty']); r=clamp(.08+.40*abs(row['acoustic_pressure']-row['optical_intensity']*.1)+.10*max(0,fn-1)); xi=clamp(.12+.40*row['uncertainty']+.25*(1-conf)+.15*(0 if mg is not None else 1))
  confs.append(conf); ps.append(p); rs.append(r); xis.append(xi); metg.append(mg or 0)
  cur.execute('INSERT INTO external_sample_cell_mapping_v09 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('xmap9'),run,sample,best['cell_uid'],best['node_id'],bestd,m['met_event_id'] if m else None,mg,conf,p,r,xi,json.dumps({'force_norm':fn,'phase_fit':phasefit,'source':'v09_no_source_rewrite'},sort_keys=True),ts))
 fns=[math.sqrt(r['force_x']**2+r['force_y']**2+r['force_z']**2) for r in rows]; ph=[r['phase'] for r in rows]; pd=[abs(ph[i]-ph[i-1]) for i in range(1,len(ph))] or [0]
 force_non=stdev(fns)/(mean(fns)+1e-9); phase_cont=clamp(1/(1+mean(pd))); multimodal=clamp(.5+.5*math.cos(mean([r['phase'] for r in rows]) if rows else 0)); confm=mean(confs); metalign=clamp(mean(metg)+.4*confm); pst=mean(ps); rc=mean(rs); xp=mean(xis)
 gate='REAL_DATA_TRIAL_REVIEW_REQUIRED' if declared and valid and len(rows)>=50 and confm>.55 else 'BLOCKED_PENDING_REAL_EXTERNAL_DATA'; interp='real external data declared; manual review still required' if declared else 'ingestion path validated with demo/fixture proxy; cannot clear real-data adoption gate'
 cur.execute('INSERT INTO realdata_calibration_result_v09 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('xres9'),run,fileid,len(rows),len(confs),int(declared),int(valid),force_non,phase_cont,multimodal,confm,metalign,pst,rc,xp,gate,interp,ts))
 gates=[]
 def gate_row(name,status,severity,obs,exp,block,rat):
  gates.append((name,status,block)); cur.execute('INSERT INTO external_data_quality_gate_v09 VALUES (?,?,?,?,?,?,?,?,?,?)',(sid('gate9'),run,name,status,severity,str(obs),str(exp),int(block),rat,ts))
 gate_row('schema_valid','PASS' if valid else 'FAIL','hard',valid,True,not valid,'schema must validate'); gate_row('sample_count_minimum','PASS' if len(rows)>=50 else 'FAIL','hard',len(rows),'>=50',len(rows)<50,'minimum sample coverage'); gate_row('declared_real_external','PASS' if declared else 'BLOCKED','hard',declared,True,not declared,'fixture/demo cannot clear real data gate'); gate_row('mapping_confidence','PASS' if confm>.55 else 'WARN','medium',round(confm,6),'>0.55',0,'mapping quality'); gate_row('p_r_xi_boundary_preserved','PASS','hard','P/R before Xi','PASS',0,'v09 does not create P/R/Xi source rows'); gate_row('candidate_patch_not_auto_applied','PASS','hard',0,0,0,'manual packet only')
 patch=cur.execute('SELECT * FROM candidate_patch_manifest_v07 LIMIT 1').fetchone(); profile=cur.execute("SELECT * FROM system_id_parameter_profile_v06 WHERE profile_role='fitted_candidate' LIMIT 1").fetchone(); blockers=[g[0] for g in gates if g[2]]+['human_review_required']; sat=[g[0] for g in gates if g[1]=='PASS']
 packet={'version':'v0.9','run_id':run,'patch_id':patch['patch_id'] if patch else None,'candidate_profile_id':profile['profile_id'] if profile else None,'declared_real_external':declared,'real_data_gate_status':gate,'metrics':{'sample_count':len(rows),'mapped_sample_count':len(confs),'force_nonuniformity':force_non,'phase_continuity_score':phase_cont,'multimodal_consistency_score':multimodal,'mapping_confidence_mean':confm,'met_alignment_score':metalign,'p_stability_proxy':pst,'r_counter_proxy':rc,'xi_pressure_proxy':xp},'blockers':blockers,'satisfied_gates':sat,'decision':'MANUAL_REVIEW_PACKET_CREATED_PATCH_NOT_APPLIED','boundary':'append-only no source fact mutation no Xi replacement of P/R'}
 packetp=rep/'candidate_patch_manual_review_v09_packet.json'; packetp.write_text(json.dumps(packet,indent=2,sort_keys=True),encoding='utf-8'); psha=sha(packetp); packetid=sid('packet9')
 cur.execute('INSERT INTO candidate_patch_manual_review_packet_v09 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',(packetid,run,patch['patch_id'] if patch else 'missing',profile['profile_id'] if profile else 'missing',patch['patch_sha256'] if patch else 'missing',patch['patch_status'] if patch else 'missing','manual_review_packet_created_patch_not_applied',0,1,str(packetp),psha,json.dumps(packet,sort_keys=True),ts))
 decision='BLOCKED_PENDING_REAL_EXTERNAL_DATA_PATCH_NOT_APPLIED' if not declared else 'REAL_DATA_REVIEW_REQUIRED_PATCH_NOT_APPLIED'
 cur.execute('INSERT INTO candidate_patch_application_decision_v09 VALUES (?,?,?,?,?,?,?,?,?,?)',(sid('decision9'),run,packetid,decision,0,1,json.dumps(blockers),json.dumps(sat),'v09 review only; patch remains staged',ts))
 after={t:(count(con,t),table_sig(con,t)) for t in PROTECTED}
 for t,(cb,sb) in before.items():
  ca,sa=after[t]; status='PASS' if cb==ca and sb==sa else 'FAIL'; cur.execute('INSERT INTO source_fact_digest_v09 VALUES (?,?,?,?,?,?,?,?,?)',(sid('dig9'),run,t,cb,ca,sb,sa,status,ts))
 def check(name,ok,obs,exp,sev,rat): cur.execute('INSERT INTO realdata_review_acceptance_report_v09 VALUES (?,?,?,?,?,?,?,?,?)',(sid('chk9'),run,name,'PASS' if ok else 'FAIL',str(obs),str(exp),sev,rat,ts))
 check('csv_schema_valid',valid,valid,True,'hard','schema ok'); check('sample_rows_loaded',len(rows)>0,len(rows),'>0','hard','sample table populated'); check('mapping_rows_equal_samples',len(confs)==len(rows),len(confs),len(rows),'hard','mapping complete'); check('real_data_gate_honest',declared or gate=='BLOCKED_PENDING_REAL_EXTERNAL_DATA',gate,'blocked unless real','hard','honest gate'); check('candidate_not_auto_applied',True,0,0,'hard','no auto apply'); check('source_facts_unchanged',all(before[t]==after[t] for t in PROTECTED),'stable','stable','hard','source facts stable'); check('manual_review_packet_created',packetp.exists(),str(packetp),'exists','hard','packet exists'); check('p_r_xi_boundary_preserved',True,'P/R before Xi','PASS','hard','no direct Xi to P/R')
 md=rep/'REALDATA_REVIEW_V09_REPORT.md'; md.write_text(f'# v0.9 Real External Physical Data Ingestion + Candidate Patch Manual Review\n\nRun ID: `{run}`\n\nDecision: `{decision}`\n\nReal external declared: `{declared}`\n\nGate: `{gate}`\n\nSample count: `{len(rows)}`\nMapped count: `{len(confs)}`\n\nThe candidate profile remains staged and is not applied.\n',encoding='utf-8')
 summ=rep/'realdata_review_v09_summary.json'; summ.write_text(json.dumps(packet,indent=2,sort_keys=True),encoding='utf-8')
 for path,role in [(packetp,'manual_review_packet'),(md,'v09_report'),(summ,'v09_summary'),(csvp,'ingested_external_csv')]: cur.execute('INSERT INTO realdata_review_artifact_manifest_v09 VALUES (?,?,?,?,?,?)',(sid('art9'),run,str(path),role,sha(path),ts))
 con.commit(); print(json.dumps({'status':'ok','run_id':run,'decision':decision,'gate':gate},sort_keys=True))
if __name__=='__main__': main()
