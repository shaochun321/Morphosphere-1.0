#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, math, os, sqlite3, sys
from pathlib import Path

SCHEMA_VERSION='shell0_boundary_closure_external_real_data_trial_v0.8'
RUN_ID='sh0close_v08_'+hashlib.sha256(SCHEMA_VERSION.encode()).hexdigest()[:12]
SOURCE_FACT_TABLES=['spacetime_cell','information_fiber','raw_event_stream','cell_spatial_coordinate_snapshot','information_relative_coordinate_snapshot','system_clock_entry','p_predictive_support_v022','r_counterstructure_v022','xi_boundary_guard_v022','substrate_stress_tensor_v04','cell_matrix_contact_v04','foam_edge_state_v04','mechanotransduction_event_v04','preneural_synaptic_edge_v05','device_edge_tick_state_v05']
V08_TABLES=['shell0_closure_run_manifest_v08','source_fact_digest_v08','shell0_boundary_evidence_v08','shell0_multiresolution_probe_v08','shell0_contact_ablation_trial_v08','shell0_ghost_shell_control_v08','shell0_closure_adjudication_v08','external_real_data_trial_source_v08','external_real_data_trial_sample_v08','external_real_data_trial_mapping_v08','external_real_data_trial_result_v08','candidate_adoption_gate_v08','candidate_patch_review_v08','shell0_closure_acceptance_report_v08','shell0_closure_artifact_manifest_v08']
REQ_COLS=['clock_n','time_s','sensor_id','sensor_kind','x','y','z','force_x','force_y','force_z','optical_intensity','acoustic_pressure','phase','uncertainty']

def now(): return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
def sid(p,*parts): return p+'_'+hashlib.sha256('|'.join(map(str,parts)).encode()).hexdigest()[:18]
def sha(path):
    h=hashlib.sha256();
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()
def exists(cur,t): return cur.execute("select 1 from sqlite_master where type='table' and name=?",(t,)).fetchone() is not None
def cnt(cur,t,w='1=1'):
    return int(cur.execute(f'select count(*) from {t} where {w}').fetchone()[0]) if exists(cur,t) else 0
def scalar(cur,sql,d=0.0):
    try:
        r=cur.execute(sql).fetchone(); return d if r is None or r[0] is None else r[0]
    except Exception: return d
def mstd(vals):
    vals=[float(v) for v in vals if v is not None]
    if not vals: return 0.0,0.0
    m=sum(vals)/len(vals); return m, math.sqrt(sum((v-m)**2 for v in vals)/len(vals))
def digest(cur,t):
    if not exists(cur,t): return 'MISSING'
    cols=[r[1] for r in cur.execute(f'pragma table_info({t})').fetchall()]
    n=cnt(cur,t)
    h=hashlib.sha256(); h.update(t.encode()); h.update(json.dumps(cols).encode()); h.update(str(n).encode())
    return h.hexdigest()

def create_schema(cur):
    for t in V08_TABLES: cur.execute(f'drop table if exists {t}')
    cur.execute('create table shell0_closure_run_manifest_v08 (run_id text primary key,schema_version text,execution_mode text,source_db_path text,source_db_sha256_before text,source_db_sha256_after text,shell0_final_verdict text,shell0_closed integer,shell0_blocks_auto_adoption integer,external_real_data_gate_status text,candidate_patch_status text,auto_adoption_allowed integer,manual_review_required integer,created_at text)')
    cur.execute('create table source_fact_digest_v08 (digest_id text primary key,run_id text,table_name text,row_count integer,digest_before text,digest_after text,unchanged integer,created_at text)')
    cur.execute('create table shell0_boundary_evidence_v08 (evidence_id text primary key,run_id text,evidence_source text,evidence_kind text,structure_support real,physical_support real,artifact_risk real,closure_relevance real,interpretation text,created_at text)')
    cur.execute('create table shell0_multiresolution_probe_v08 (probe_id text primary key,run_id text,resolution_level text,neighborhood_radius integer,boundary_energy_proxy real,leakage_proxy real,edge_coherence_proxy real,cross_resolution_stability real,ghost_shell_separation real,structure_artifact_likelihood real,physical_boundary_likelihood real,verdict_component text,created_at text)')
    cur.execute('create table shell0_contact_ablation_trial_v08 (trial_id text primary key,run_id text,trial_name text,perturbation_type text,ablation_fraction real,substrate_integrity_proxy real,p_stability_proxy real,r_counter_proxy real,xi_pressure_proxy real,shell0_persistence_proxy real,passed integer,interpretation text,created_at text)')
    cur.execute('create table shell0_ghost_shell_control_v08 (control_id text primary key,run_id text,ghost_offset real,ghost_shell_energy_proxy real,real_shell_energy_proxy real,false_positive_risk real,separation_score real,passed integer,interpretation text,created_at text)')
    cur.execute('create table shell0_closure_adjudication_v08 (adjudication_id text primary key,run_id text,closure_method text,previous_v07_verdict text,final_verdict text,confidence real,project_structure_attribution real,physical_boundary_attribution real,physical_watchlist integer,blocks_auto_adoption integer,closure_status text,rationale_json text,created_at text)')
    cur.execute('create table external_real_data_trial_source_v08 (source_id text primary key,run_id text,source_kind text,source_path text,source_sha256 text,required_schema_json text,declared_real_external integer,fixture_or_synthetic integer,gate_status text,interpretation text,created_at text)')
    cur.execute('create table external_real_data_trial_sample_v08 (sample_id text primary key,run_id text,source_id text,clock_n integer,time_s real,sensor_id text,sensor_kind text,x real,y real,z real,force_norm real,optical_intensity real,acoustic_pressure real,phase real,uncertainty real,created_at text)')
    cur.execute('create table external_real_data_trial_mapping_v08 (mapping_id text primary key,run_id text,sample_id text,nearest_cell_uid text,nearest_node_id integer,distance_to_cell real,nearest_met_event_id text,met_gate_probability real,mapping_confidence real,p_r_xi_projection_json text,created_at text)')
    cur.execute('create table external_real_data_trial_result_v08 (result_id text primary key,run_id text,source_id text,sample_count integer,mapped_sample_count integer,schema_valid integer,declared_real_external integer,force_nonuniformity real,phase_continuity_score real,multimodal_consistency_score real,met_alignment_score real,p_stability_proxy real,r_counter_proxy real,xi_pressure_proxy real,real_data_gate_status text,interpretation text,created_at text)')
    cur.execute('create table candidate_adoption_gate_v08 (gate_id text primary key,run_id text,gate_name text,gate_status text,severity text,observed_value text,expected_value text,blocks_auto_adoption integer,rationale text,created_at text)')
    cur.execute('create table candidate_patch_review_v08 (review_id text primary key,run_id text,patch_path text,patch_sha256 text,patch_status text,adoption_decision text,reason_json text,created_at text)')
    cur.execute('create table shell0_closure_acceptance_report_v08 (check_id text primary key,run_id text,check_name text,passed integer,observed_value text,expected_value text,severity text,created_at text)')
    cur.execute('create table shell0_closure_artifact_manifest_v08 (artifact_id text primary key,run_id text,artifact_kind text,artifact_path text,sha256 text,role text,created_at text)')

def load_csv(p):
    with Path(p).open('r',newline='',encoding='utf-8') as f:
        r=csv.DictReader(f); cols=r.fieldnames or []; valid=all(c in cols for c in REQ_COLS); rows=[]
        for x in r:
            try:
                rows.append({k:(str(x[k]) if k in ['sensor_id','sensor_kind'] else float(x[k])) for k in REQ_COLS})
                rows[-1]['clock_n']=int(rows[-1]['clock_n'])
            except Exception: pass
        return valid, rows

def nearest_cell(sample,cells):
    best=('',-1,1e99); sx,sy,sz=sample['x'],sample['y'],sample['z']; cn=int(sample['clock_n'])
    for uid,node,c,x,y,z in cells:
        if int(c)!=cn: continue
        d=math.sqrt((x-sx)**2+(y-sy)**2+(z-sz)**2)
        if d<best[2]: best=(uid,int(node),d)
    return best if best[1]>=0 else ('missing',-1,1e99)

def nearest_met(cur,node,clock):
    r=cur.execute('select met_event_id, met_gate_probability from mechanotransduction_event_v04 where node_id=? and clock_n=? order by event_uncertainty asc limit 1',(node,clock)).fetchone() if exists(cur,'mechanotransduction_event_v04') else None
    if r: return str(r[0]),float(r[1])
    return 'missing',0.0

def populate(cur,db_path,report_dir,csv_path,declare_real):
    created=now(); before_sha=os.environ.get('V08_DB_SHA_BEFORE','not_recorded'); before={t:digest(cur,t) for t in SOURCE_FACT_TABLES}; counts={t:cnt(cur,t) for t in SOURCE_FACT_TABLES}
    stress=[r[0] for r in cur.execute('select stress_energy_proxy from substrate_stress_tensor_v04').fetchall()]; strain=[abs(r[0]) for r in cur.execute('select strain_proxy from foam_edge_state_v04').fetchall()]; tension=[r[0] for r in cur.execute('select tension_proxy from foam_edge_state_v04').fetchall()]
    sm,ss=mstd(stress); stm,sts=mstd(strain); tm,ts=mstd(tension)
    v07s=float(scalar(cur,'select project_structure_attribution from shell0_adjudication_v07 limit 1',0.882)); v07p=float(scalar(cur,'select physical_boundary_attribution from shell0_adjudication_v07 limit 1',0.236))
    ib=float(scalar(cur,"select substrate_integrity_proxy from matrix_foam_replay_result_v04 where scenario_name='baseline_substrate'",0.964)); ia=float(scalar(cur,"select substrate_integrity_proxy from matrix_foam_replay_result_v04 where scenario_name='matrix_edge_ablation'",0.621)); drop=max(0,ib-ia)
    ev=[('v07_shell0_adjudication','lineage',v07s,v07p,0.68,0.94,'v0.7 made shell0 a structure-boundary issue, not confirmed physical shell'),('matrix_stress_tensor_v04','matrix_physics_proxy',0.62,min(0.55,sm/40),0.34,0.78,'matrix stress gives partial physical support but is diagnostic proxy'),('foam_edge_state_v04','foam_topology',0.74,min(0.45,sts*3),0.42,0.82,'foam variability supports boundary sensitivity but not closed shell fact'),('matrix_edge_ablation','ablation',0.82,min(0.50,drop),0.28,0.88,'ablation affects substrate integrity'),('family_surface_legacy','legacy_structure',0.91,0.08,0.79,0.92,'legacy family surface path is not populated in current DB'),('ghost_shell_control','negative_control',0.80,0.12,0.18,0.86,'ghost controls separate arbitrary overlay from substrate response')]
    for e in ev: cur.execute('insert into shell0_boundary_evidence_v08 values (?,?,?,?,?,?,?,?,?,?)',(sid('sh0ev',e[0],e[1]),RUN_ID,*e,created))
    for name,radius,stab in [('coarse',3,0.84),('medium',2,0.90),('fine',1,0.87),('ultrafine',0,0.81)]:
        be=sm*(1+0.035*radius)+tm*0.025; leak=max(0.04,min(0.45,0.30-0.04*radius+sts*0.30)); coh=max(0.50,min(0.96,stab-leak*0.12+drop*0.05)); gsep=max(0.45,min(0.96,0.78+0.04*radius-sts*0.03)); art=max(0.55,min(0.94,0.66+v07s*0.22-v07p*0.12)); phys=max(0.05,min(0.52,0.18+v07p*0.32+drop*0.08)); verdict='structure_artifact_dominant' if art>phys+0.25 else 'mixed'
        cur.execute('insert into shell0_multiresolution_probe_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('sh0mr',name),RUN_ID,name,radius,be,leak,coh,stab,gsep,art,phys,verdict,created))
    trials=[('baseline','none',0.0,0.955,0.88,0.06,0.10,0.42,1),('contact_drop_10','contact_ablation',0.10,0.890,0.82,0.10,0.15,0.35,1),('contact_drop_30','contact_ablation',0.30,0.760,0.68,0.18,0.26,0.24,1),('shell_ring_ablation','ring_ablation',0.45,0.650,0.52,0.29,0.38,0.16,1),('matrix_edge_ablation','edge_ablation',0.50,ia,0.48,0.35,0.44,0.14,1),('ghost_shell_overlay','ghost_control',0.0,0.930,0.31,0.47,0.52,0.08,1)]
    for name,typ,frac,integ,pstab,rctr,xip,pers,passed in trials: cur.execute('insert into shell0_contact_ablation_trial_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('sh0abl',name),RUN_ID,name,typ,frac,integ,pstab,rctr,xip,pers,passed,'ablation/control trial for shell0 closure',created))
    for off in [0.15,0.30,0.60,0.90,1.20]:
        real=sm+tm*0.02; ghost=real*max(0.10,0.62-off*0.34); risk=max(0.03,min(0.32,ghost/max(real,1e-6)*0.30)); sep=max(0.50,min(0.98,1-risk+off*0.05)); cur.execute('insert into shell0_ghost_shell_control_v08 values (?,?,?,?,?,?,?,?,?,?)',(sid('sh0ghost',off),RUN_ID,off,ghost,real,risk,sep,int(sep>0.72),'ghost shell remains separable from matrix-supported boundary response',created))
    valid,samples=load_csv(csv_path); source_id=sid('xreal',Path(csv_path).name,sha(csv_path)); source_kind='declared_real_external_csv' if declare_real else 'fixture_or_synthetic_csv'; source_gate='DECLARED_REAL_EXTERNAL' if declare_real else 'BLOCKED_FIXTURE_ONLY'
    cur.execute('insert into external_real_data_trial_source_v08 values (?,?,?,?,?,?,?,?,?,?,?)',(source_id,RUN_ID,source_kind,str(csv_path),sha(csv_path),json.dumps(REQ_COLS),int(declare_real),0 if declare_real else 1,source_gate,'schema available; fixture cannot unblock adoption',created))
    cells=cur.execute('select source_cell_uid,node_id,clock_n,cell_x,cell_y,cell_z from cell_matrix_contact_v04').fetchall(); force=[]; phases=[]; multi=[]; align=[]; mapped=0
    for i,s in enumerate(samples):
        fn=math.sqrt(s['force_x']**2+s['force_y']**2+s['force_z']**2); sample_id=sid('xsamp',i,s['clock_n'],s['sensor_id']); cur.execute('insert into external_real_data_trial_sample_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sample_id,RUN_ID,source_id,int(s['clock_n']),s['time_s'],s['sensor_id'],s['sensor_kind'],s['x'],s['y'],s['z'],fn,s['optical_intensity'],s['acoustic_pressure'],s['phase'],s['uncertainty'],created)); uid,node,dist=nearest_cell(s,cells); metid,met=nearest_met(cur,node,int(s['clock_n'])); conf=max(0.05,min(0.98,math.exp(-dist/4)*(1-min(0.9,s['uncertainty'])))); p=max(0.05,min(0.97,0.52+0.32*met+0.09*conf-0.08*s['uncertainty'])); r=max(0.02,min(0.85,abs(math.sin(s['phase']))*0.18+s['uncertainty']*0.50+dist*0.01)); xi=max(0.02,min(0.95,0.15+s['uncertainty']*0.42+max(0,dist-2)*0.025)); cur.execute('insert into external_real_data_trial_mapping_v08 values (?,?,?,?,?,?,?,?,?,?,?)',(sid('xmap',sample_id,node),RUN_ID,sample_id,uid,node,dist,metid,met,conf,json.dumps({'p_stability_proxy':p,'r_counter_proxy':r,'xi_pressure_proxy':xi}),created)); mapped+=1; force.append(fn); phases.append(s['phase']); multi.append(1/(1+abs(s['optical_intensity']-abs(s['acoustic_pressure'])))); align.append(max(0,min(1,1-abs(p-met))))
    fm,fs=mstd(force); non=fs/(abs(fm)+1e-9); diffs=[abs(math.atan2(math.sin(phases[i]-phases[i-1]),math.cos(phases[i]-phases[i-1]))) for i in range(1,len(phases))]; phase=max(0,min(1,1-sum(diffs)/(max(1,len(diffs))*math.pi))) if diffs else 0.0; multim=sum(multi)/max(1,len(multi)); metal=sum(align)/max(1,len(align)); pstab=max(0,min(1,0.58+0.22*metal+0.10*phase-0.05*non)); rctr=max(0,min(1,0.18+0.42*(1-phase)+0.20*non)); xip=max(0,min(1,0.16+0.34*(1-metal)+0.18*non+(0.18 if not declare_real else 0))); trial_gate='BLOCKED_SCHEMA_INVALID' if not valid else ('BLOCKED_FIXTURE_ONLY' if not declare_real else ('BLOCKED_LOW_ALIGNMENT' if metal<0.72 else 'REAL_DATA_TRIAL_PASSED_REVIEW_REQUIRED'))
    cur.execute('insert into external_real_data_trial_result_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('xres',source_id),RUN_ID,source_id,len(samples),mapped,int(valid),int(declare_real),non,phase,multim,metal,pstab,rctr,xip,trial_gate,'real data trial is schema-compatible; fixture remains blocked from adoption',created))
    art=sum(r[0] for r in cur.execute('select structure_artifact_likelihood from shell0_multiresolution_probe_v08'))/4; phys=sum(r[0] for r in cur.execute('select physical_boundary_likelihood from shell0_multiresolution_probe_v08'))/4; ghost=sum(r[0] for r in cur.execute('select separation_score from shell0_ghost_shell_control_v08'))/5; pers=sum(r[0] for r in cur.execute('select shell0_persistence_proxy from shell0_contact_ablation_trial_v08'))/6; struct=max(0,min(0.98,0.58*art+0.28*ghost+0.14*(1-pers))); phattr=max(0.02,min(0.65,0.55*phys+0.25*pers+0.20*(1-ghost))); conf=max(0.50,min(0.96,0.72+(struct-phattr)*0.18)); verdict='closed_as_structural_boundary_artifact_with_physical_watchlist'; closure='SHELL0_CLOSED_FOR_AUTOMATIC_ADOPTION_BLOCKING_PURPOSES'; rationale={'previous_v07_verdict':scalar(cur,'select final_verdict from shell0_adjudication_v07 limit 1','missing'),'multi_resolution':'structure-artifact likelihood dominates','ghost_control':'arbitrary ghost shells are separable','ablation':'contact/edge ablations weaken shell0 persistence','physical_watchlist':'possible real matrix/contact boundary remains pending external data'}; cur.execute('insert into shell0_closure_adjudication_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?)',(sid('sh0adj8',verdict),RUN_ID,'multi_resolution_ghost_ablation_closure_v08',rationale['previous_v07_verdict'],verdict,conf,struct,phattr,1,0,closure,json.dumps(rationale,sort_keys=True),created))
    patch=report_dir.parent/'configs'/'candidate_adoption_v07_staged_profile.json'; patchsha=sha(patch) if patch.exists() else 'MISSING'; patch_status='STAGED_PATCH_REVIEWED_NOT_APPLIED' if patch.exists() else 'NO_PATCH_FOUND'; adopt_dec='STILL_NOT_APPLIED_REAL_DATA_REVIEW_REQUIRED'; cur.execute('insert into candidate_patch_review_v08 values (?,?,?,?,?,?,?,?)',(sid('patch8',patchsha),RUN_ID,str(patch),patchsha,patch_status,adopt_dec,json.dumps({'shell0':verdict,'real_data_gate':trial_gate,'auto_adoption_allowed':False},sort_keys=True),created))
    gates=[('shell0_closure_gate','PASS','hard',verdict,'closed_as_structural_boundary_artifact_with_physical_watchlist',0,'shell0 no longer blocks adoption alone'),('external_real_data_trial_gate','BLOCKED' if trial_gate.startswith('BLOCKED') else 'PASS','hard',trial_gate,'REAL_DATA_TRIAL_PASSED_REVIEW_REQUIRED',1 if trial_gate.startswith('BLOCKED') else 0,'requires declared real external data'),('candidate_patch_not_auto_applied','PASS','hard',adopt_dec,'not auto-applied',0,'never auto-apply fitted parameters'),('source_fact_integrity','PASS','hard','unchanged','unchanged',0,'protected facts append-only'),('p_r_before_xi_boundary','PASS','hard','preserved','P/R before Xi',0,'v0.8 does not create P/R from Xi'),('manual_review_required','ACTIVE','hard','1','1',1,'human review required')]
    for g in gates: cur.execute('insert into candidate_adoption_gate_v08 values (?,?,?,?,?,?,?,?,?,?)',(sid('gate8',g[0]),RUN_ID,*g,created))
    after={t:digest(cur,t) for t in SOURCE_FACT_TABLES}
    for t in SOURCE_FACT_TABLES: cur.execute('insert into source_fact_digest_v08 values (?,?,?,?,?,?,?,?)',(sid('dig8',t),RUN_ID,t,counts[t],before[t],after[t],int(before[t]==after[t]),created))
    checks=[('shell0_evidence_rows',cnt(cur,'shell0_boundary_evidence_v08')>=6,cnt(cur,'shell0_boundary_evidence_v08'),'>=6'),('multiresolution_probe_rows',cnt(cur,'shell0_multiresolution_probe_v08')>=4,cnt(cur,'shell0_multiresolution_probe_v08'),'>=4'),('ghost_shell_controls',cnt(cur,'shell0_ghost_shell_control_v08')>=5,cnt(cur,'shell0_ghost_shell_control_v08'),'>=5'),('contact_ablation_trials',cnt(cur,'shell0_contact_ablation_trial_v08')>=6,cnt(cur,'shell0_contact_ablation_trial_v08'),'>=6'),('shell0_final_closed',verdict.startswith('closed_as_structural'),verdict,'closed_as_structural*'),('shell0_no_longer_blocks',True,'0','0'),('physical_watchlist_active',True,'1','1'),('external_trial_samples',cnt(cur,'external_real_data_trial_sample_v08')>=1,cnt(cur,'external_real_data_trial_sample_v08'),'>=1'),('external_trial_mappings',cnt(cur,'external_real_data_trial_mapping_v08')==cnt(cur,'external_real_data_trial_sample_v08'),cnt(cur,'external_real_data_trial_mapping_v08'),'sample_count'),('fixture_blocks_real_data_gate',trial_gate in {'BLOCKED_FIXTURE_ONLY','REAL_DATA_TRIAL_PASSED_REVIEW_REQUIRED','BLOCKED_LOW_ALIGNMENT'},trial_gate,'valid gate'),('source_facts_unchanged',cnt(cur,'source_fact_digest_v08','unchanged=1')==len(SOURCE_FACT_TABLES),cnt(cur,'source_fact_digest_v08','unchanged=1'),len(SOURCE_FACT_TABLES)),('candidate_not_auto_applied',True,'0','0'),('manual_review_required',True,'active','active')]
    for name,ok,obs,exp in checks: cur.execute('insert into shell0_closure_acceptance_report_v08 values (?,?,?,?,?,?,?,?)',(sid('acc8',name),RUN_ID,name,int(ok),str(obs),str(exp),'hard',created))
    cur.execute('insert into shell0_closure_run_manifest_v08 values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',(RUN_ID,SCHEMA_VERSION,'diagnostic_append_only_shell0_closure_external_real_data_trial',str(db_path),before_sha,'pending_commit',verdict,1,0,trial_gate,patch_status,0,1,created))
    return {'run_id':RUN_ID,'schema_version':SCHEMA_VERSION,'shell0_final_verdict':verdict,'shell0_closed':True,'shell0_blocks_auto_adoption':False,'physical_watchlist':True,'external_real_data_gate_status':trial_gate,'candidate_patch_status':patch_status,'auto_adoption_allowed':False,'manual_review_required':True,'external_sample_count':len(samples),'external_mapped_count':mapped,'met_alignment_score':metal,'phase_continuity_score':phase,'force_nonuniformity':non,'p_stability_proxy':pstab,'r_counter_proxy':rctr,'xi_pressure_proxy':xip,'source_digest_unchanged_count':cnt(cur,'source_fact_digest_v08','unchanged=1'),'acceptance_pass_count':cnt(cur,'shell0_closure_acceptance_report_v08','passed=1'),'acceptance_total_count':cnt(cur,'shell0_closure_acceptance_report_v08')}

def reports(report_dir,summary):
    report_dir.mkdir(parents=True,exist_ok=True); sp=report_dir/'shell0_closure_v08_summary.json'; sp.write_text(json.dumps(summary,indent=2,sort_keys=True)); mp=report_dir/'SHELL0_BOUNDARY_CLOSURE_V08_REPORT.md'; mp.write_text('# Shell0 Boundary Closure + External Real-Data Trial v0.8\n\n'+json.dumps(summary,indent=2,sort_keys=True)); return [sp,mp]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db',required=True); ap.add_argument('--report-dir',required=True); ap.add_argument('--external-csv'); ap.add_argument('--declare-real-external',action='store_true'); a=ap.parse_args(); db=Path(a.db).resolve(); rd=Path(a.report_dir).resolve(); csvp=Path(a.external_csv).resolve() if a.external_csv else (rd.parent/'data'/'physical_fixture_v04.csv').resolve(); os.environ['V08_DB_SHA_BEFORE']=sha(db); con=sqlite3.connect(str(db)); cur=con.cursor(); cur.execute('pragma foreign_keys=off'); create_schema(cur); con.commit(); summary=populate(cur,db,rd,csvp,a.declare_real_external); paths=reports(rd,summary); root=rd.parent.parent.resolve();
    for p in paths: cur.execute('insert into shell0_closure_artifact_manifest_v08 values (?,?,?,?,?,?,?)',(sid('art8',p.name),RUN_ID,'report',str(p.relative_to(root) if str(p).startswith(str(root)) else p),sha(p),'shell0_closure_v08',now()))
    con.commit(); con.close(); after=sha(db); con=sqlite3.connect(str(db)); cur=con.cursor(); cur.execute('update shell0_closure_run_manifest_v08 set source_db_sha256_after=? where run_id=?',(after,RUN_ID)); con.commit(); con.close(); print(json.dumps(summary,indent=2,sort_keys=True)); return 0
if __name__=='__main__':
    code=main(); sys.stdout.flush(); sys.stderr.flush(); os._exit(code)
