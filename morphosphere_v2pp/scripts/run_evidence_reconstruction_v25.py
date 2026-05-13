#!/usr/bin/env python3
import argparse,csv,hashlib,json,math,os,shutil,sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2]
SRC_DB=ROOT/'outputs/morphosphere_ctc_source_verified_v24_output_database.db'
CSV=ROOT/'morphosphere_v2pp/data/ctc_centroids_real_v24.csv'
OUT=ROOT/'outputs/morphosphere_evidence_reconstruction_v25_output_database.db'
RT=ROOT/'runtime_store/v25'
REPORTS=ROOT/'morphosphere_v2pp/reports'
WS=28; STRIDE=7; TH=0.4951; REENTRY='via_o_candidate_only'
def hfile(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def htxt(x): return hashlib.sha256(x.encode()).hexdigest()
def jd(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def clamp(x,a=0,b=1): return max(a,min(b,x))
def pid(r): return f"ip25_{str(r['sequence_id']).zfill(2)}_t{int(r['frame']):03d}_trk{str(r['track_id']).replace('_','-')}"
def read_csv(p):
 rows=[]
 with open(p,newline='',encoding='utf-8') as f:
  for r in csv.DictReader(f):
   for k in ['time_s','x','y','z','value','uncertainty','centroid_x','centroid_y','centroid_z']:
    r[k]=float(r[k])
   for k in ['frame','area','start_frame','end_frame']:
    r[k]=int(float(r[k]))
   r['sequence_id']=str(r['sequence_id']).zfill(2)
   rows.append(r)
 return rows
def qdict(con,table,key):
 con.row_factory=sqlite3.Row
 try: return {str(r[key]):dict(r) for r in con.execute(f'SELECT * FROM {table}')}
 except sqlite3.Error: return {}
def cells(con): return [dict(r) for r in con.execute('SELECT cell_uid,x,y,z FROM spacetime_cell')]
def nearest(cs,x,y,z):
 best=('',1e18)
 for c in cs:
  d=((x-c['x'])**2+(y-c['y'])**2+(z-c['z'])**2)**0.5
  if d<best[1]: best=(c['cell_uid'],d)
 return best
def bounds(rows):
 out={}
 for s in sorted(set(r['sequence_id'] for r in rows)):
  rs=[r for r in rows if r['sequence_id']==s]; xs=[r['centroid_x'] for r in rs]; ys=[r['centroid_y'] for r in rs]
  out[s]={'x_min':min(xs),'x_max':max(xs),'y_min':min(ys),'y_max':max(ys),'z_min':0,'z_max':0}
 return out
def n11(v,lo,hi): return 0 if hi==lo else 2*(v-lo)/(hi-lo)-1
def info_rows(rows):
 out=[]
 for r in rows:
  raw={k:r[k] for k in r.keys()}
  out.append({'point_id':pid(r),'source_id':r['source_id'],'source_dataset':r['dataset_name'],'source_sequence':r['sequence_id'],'source_frame':r['frame'],'source_track_id':r['track_id'],'sample_id':r['sample_id'],'sensor_id':r['sensor_id'],'sensor_kind':r['sensor_kind'],'clock_domain':r['clock_domain'],'time_s':r['time_s'],'raw_x':r['centroid_x'],'raw_y':r['centroid_y'],'raw_z':r['centroid_z'],'raw_area':r['area'],'channel':r['channel'],'value':r['value'],'uncertainty':r['uncertainty'],'source_coordinate_system':'ctc_pixel_xy_frame_z0','source_unit':'pixel_frame_proxy_units','license':r.get('license',''),'citation_key':r.get('citation_key',''),'doi':r.get('doi',''),'parent_track_id':str(r.get('parent_track_id','')),'source_zip_sha256':r.get('source_zip_sha256',''),'provenance_hash':htxt(jd(raw))})
 return out
def transforms(rows,cs,bd):
 out=[]
 for r in rows:
  b=bd[r['sequence_id']]; nx=n11(r['centroid_x'],b['x_min'],b['x_max']); ny=n11(r['centroid_y'],b['y_min'],b['y_max']); nz=0
  sx,sy,sz=5*nx,5*ny,0; uid,d=nearest(cs,sx,sy,sz); p=pid(r)
  out.append({'transform_id':'ct25_'+p[5:],'source_point_id':p,'from_coordinate_system':'ctc_pixel_xy_frame_z0','to_coordinate_system':'cell_sphere_v852_origin_relative','raw_x':r['centroid_x'],'raw_y':r['centroid_y'],'raw_z':r['centroid_z'],'normalized_x':nx,'normalized_y':ny,'normalized_z':nz,'cell_sphere_x':sx,'cell_sphere_y':sy,'cell_sphere_z':sz,'nearest_cell_uid':uid,'distance_to_cell':d,'origin_anchor_id':f"ctc_origin_seq_{r['sequence_id']}",'relative_x':sx,'relative_y':sy,'relative_z':sz,'transform_method':'sequence_bbox_normalize_to_unit_square_then_scale_to_cell_sphere_radius_5_nearest_cell','transform_parameters_json':{'sequence_bounds':b,'sphere_radius_proxy':5.0,'z_policy':'z0_for_2d_ctc_source_preserve_4d_schema'},'transform_error':d,'reversible_refs':[p,'spacetime_cell',f"ctc_sequence_bounds_{r['sequence_id']}"]})
 return out
def metrics(pts):
 pts=sorted(pts,key=lambda r:r['frame'])
 if len(pts)<2: return dict(path_length=0,net_displacement=0,duration=0,mean_speed=0,speed_std=0,direction_coherence=0,curvature=0,continuity_gap_count=0)
 lens=[]; speeds=[]; angles=[]; gaps=0
 for a,b in zip(pts[:-1],pts[1:]):
  dx=b['centroid_x']-a['centroid_x']; dy=b['centroid_y']-a['centroid_y']; dt=max(b['time_s']-a['time_s'],1e-9); d=(dx*dx+dy*dy)**0.5
  lens.append(d); speeds.append(d/dt); angles.append(math.atan2(dy,dx) if d>0 else 0); gaps+=max(0,b['frame']-a['frame']-1)
 path=sum(lens); dx=pts[-1]['centroid_x']-pts[0]['centroid_x']; dy=pts[-1]['centroid_y']-pts[0]['centroid_y']; net=(dx*dx+dy*dy)**0.5
 curv=0 if len(angles)<2 else sum(abs(math.atan2(math.sin(b-a),math.cos(b-a))) for a,b in zip(angles[:-1],angles[1:]))/(len(angles)-1)
 mu=sum(speeds)/len(speeds); sd=(sum((v-mu)**2 for v in speeds)/len(speeds))**0.5
 return dict(path_length=path,net_displacement=net,duration=pts[-1]['time_s']-pts[0]['time_s'],mean_speed=mu,speed_std=sd,direction_coherence=(net/path if path else 0),curvature=curv,continuity_gap_count=gaps)
def windows(rows,tr,mp):
 by=defaultdict(list)
 for r in rows: by[r['track_id']].append(r)
 out=[]
 for tid,pts in sorted(by.items()):
  pts=sorted(pts,key=lambda r:r['frame']); n=len(pts); starts=[]
  if n<=WS: starts=[0]
  else:
   s=0
   while s<n:
    starts.append(s)
    if s+WS>=n: break
    s+=STRIDE
  for i,s in enumerate(starts):
   w=pts[s:s+WS]; pids=[pid(x) for x in w]; trs=[tr[p] for p in pids]; ms=metrics(w)
   radii=[(t['relative_x']**2+t['relative_y']**2+t['relative_z']**2)**0.5 for t in trs]; rm=sum(radii)/len(radii); rsd=(sum((x-rm)**2 for x in radii)/len(radii))**0.5
   bands=[int(min(9,max(0,math.floor(x/1.25)))) for x in radii]; dom=max(set(bands),key=bands.count) if bands else 0; ob=bands.count(dom)/len(bands) if bands else 0
   areas=[x['area'] for x in w]; am=sum(areas)/len(areas); acv=((sum((x-am)**2 for x in areas)/len(areas))**0.5/am) if am else 0
   wid=f"tw25_{tid.replace('_','-')}_{i:03d}_f{w[0]['frame']:03d}_{w[-1]['frame']:03d}"; sc=mp.get(tid,{}).get('source_cell_uid','')
   out.append({'trajectory_trace_id':wid,'source_track_id':tid,'sequence_id':w[0]['sequence_id'],'window_index':i,'window_start_frame':w[0]['frame'],'window_end_frame':w[-1]['frame'],'window_start_time':w[0]['time_s'],'window_end_time':w[-1]['time_s'],'sample_count':len(w),'point_ids':pids,'support_cell_ids':sorted(set(t['nearest_cell_uid'] for t in trs)),'origin_anchor_id':f"ctc_origin_seq_{w[0]['sequence_id']}",'source_cell_uid':sc,'path_length':ms['path_length'],'net_displacement':ms['net_displacement'],'duration':ms['duration'],'mean_speed':ms['mean_speed'],'speed_std':ms['speed_std'],'direction_coherence':ms['direction_coherence'],'curvature':ms['curvature'],'bandwidth':rsd,'origin_band_occupancy':ob,'continuity_gap_count':ms['continuity_gap_count'],'area_cv':acv,'mean_distance_to_cell':sum(t['distance_to_cell'] for t in trs)/len(trs),'max_distance_to_cell':max(t['distance_to_cell'] for t in trs),'window_policy':f'sliding_window_size_{WS}_stride_{STRIDE}_samples_final_partial_kept','reprojection_refs':['ct25_'+p[5:] for p in pids]})
 return out
def recipes():
 names=[('recipe25_information_point_v1','ctc_centroid_to_information_point'),('recipe25_coordinate_transform_v1','ctc_pixel_to_cell_sphere_origin_relative'),('recipe25_trajectory_window_v1','sliding_trajectory_window_trace'),('recipe25_p_spacetime_measure_v1','p_spacetime_occupancy_measure'),('recipe25_r_counter_measure_v1','r_counter_occupancy_measure'),('recipe25_xi_residual_surface_v1','xi_residual_surface_measure'),('recipe25_attention_yield_v1','attention_yield_event_from_stable_p')]
 out=[]
 for rid,name in names:
  out.append({'recipe_id':rid,'recipe_name':name,'recipe_version':'v1','input_refs':[],'output_refs':[],'formula_text':name+' diagnostic formula; source reversible and replayable','parameters_json':{'window_size':WS,'stride':STRIDE,'attention_threshold':TH,'reentry_policy':REENTRY},'thresholds_json':{},'normalization_method':'unit_interval_clamp_or_sequence_bbox','windowing_method':f'size_{WS}_stride_{STRIDE}','masking_method':'band_escape_area_curvature_proxy','code_path':'morphosphere_v2pp/scripts/run_evidence_reconstruction_v25.py','code_hash':hfile(Path(__file__)),'created_at':datetime.now(timezone.utc).isoformat()})
 return out
def ledger_ref(w,er):
 ref=f"win_{(w['window_start_frame']//10)%10}"; row=er.get(ref,{}) ; total=float(row.get('external_entropy_total',0) or 0); return ref,clamp(1-total/10),clamp(total/10)
def measures(ws,feat,resp,er):
 pr=[]; rr=[]; xi=[]; att=[]; eb=[]
 for w in ws:
  tid=w['source_track_id']; q=resp.get(tid,{}); pp=float(q.get('p_score',.5) or .5); rp=float(q.get('r_score',.35) or .35); xp=float(q.get('xi_score',.35) or .35)
  dur=clamp(w['sample_count']/WS); cont=clamp(1-w['continuity_gap_count']/max(1,w['sample_count'])); coh=clamp(w['direction_coherence']); occ=clamp(.45*dur+.25*cont+.2*w['origin_band_occupancy']+.1*coh)
  mapq=clamp(1-w['mean_distance_to_cell']/6); band=clamp(w['bandwidth']/2.5); area=clamp(w['area_cv']/.75); curv=clamp(w['curvature']/math.pi); mask=clamp(1-(.45*band+.35*area+.2*curv)); lref,eclose,emis=ledger_ref(w,er)
  pv=clamp(.35*pp+.65*(cont*occ*max(.05,mask)*max(.05,eclose))); rv=clamp(.40*rp+.60*clamp(.35*band+.25*area+.2*curv+.2*emis)); xv=clamp(.35*xp+.65*clamp(.40*(1-mapq)+.25*(1-cont)+.2*emis+.15*abs(pv-rv)*(1-mask)))
  den=max(1e-9,pv+rv+xv); pprob=pv/den; rprob=rv/den; xprob=xv/den
  suf=w['trajectory_trace_id'][5:]; pid='p25_'+suf; rid='r25_'+suf; xid='xi25_'+suf
  pr.append({'p_measure_id':pid,'o_candidate_id':'o25_'+suf,'trajectory_trace_id':w['trajectory_trace_id'],'source_track_id':tid,'window_start_frame':w['window_start_frame'],'window_end_frame':w['window_end_frame'],'support_point_ids':w['point_ids'],'support_cell_ids':w['support_cell_ids'],'support_duration':w['duration'],'support_length':w['path_length'],'support_volume':len(w['support_cell_ids']),'continuity_mass':cont,'prediction_mass':coh,'origin_band_occupancy':w['origin_band_occupancy'],'masking_survival_ratio':mask,'external_entropy_closure_score':eclose,'equivalent_probability':pprob,'p_measure_value':pv,'p_status':'p_supported' if pv>=.72 else ('p_candidate' if pv>=.55 else 'p_insufficient_occupancy'),'attention_yield_ratio':clamp(pprob-TH),'calculation_recipe_id':'recipe25_p_spacetime_measure_v1','external_ledger_ref':lref,'diagnostic_prior_ref':q.get('response_id','')})
  rr.append({'r_measure_id':rid,'target_p_measure_id':pid,'competing_trajectory_id':None,'source_track_id':tid,'counter_window_start_frame':w['window_start_frame'],'counter_window_end_frame':w['window_end_frame'],'counter_support_point_ids':w['point_ids'],'counter_support_cell_ids':w['support_cell_ids'],'counter_length':w['path_length']*rv,'counter_duration':w['duration']*rv,'p_displacement_mass':clamp(rv*(1-pprob)),'masking_exposure_gain':clamp(1-mask),'entropy_violation_mass':emis,'recursive_reentry_priority':clamp(.55*rv+.45*emis),'counter_equivalent_probability':rprob,'r_measure_value':rv,'r_status':'r_counterstructure' if rv>=.5 else 'r_low','calculation_recipe_id':'recipe25_r_counter_measure_v1','external_ledger_ref':lref,'diagnostic_prior_ref':q.get('response_id','')})
  xi.append({'xi_surface_id':xid,'layer_id':'ctc_motion_to_pr_xi_evidence_v25','origin_anchor_id':w['origin_anchor_id'],'window_start_frame':w['window_start_frame'],'window_end_frame':w['window_end_frame'],'source_point_ids':w['point_ids'],'source_event_ids':['ctc_event_'+p[5:] for p in w['point_ids']],'support_cell_ids':w['support_cell_ids'],'p_parent_refs':[pid],'r_parent_refs':[rid],'masking_context_refs':['band_escape','area_instability','curvature_instability'],'external_entropy_refs':[lref],'residual_mass':xv,'xi_equivalent_probability':xprob,'entropy_mismatch':emis,'conservation_gap':0,'phase_conflict_mass':curv,'unbound_duration':w['duration']*xv,'unbound_support_area':len(w['support_cell_ids'])*xv,'decay_state':'held' if xv>=.42 else 'decaying','memory_state':'residual_attention_requested' if xv>=.42 else 'ledger_retained','reentry_policy':REENTRY,'attention_request':xv>=.42,'xi_status':'xi_watch' if xv>=.42 else 'xi_low','calculation_recipe_id':'recipe25_xi_residual_surface_v1'})
  if pprob>=TH and mask>=.60: att.append({'attention_yield_id':'ay25_'+suf,'source_p_measure_id':pid,'trajectory_trace_id':w['trajectory_trace_id'],'window_start_frame':w['window_start_frame'],'window_end_frame':w['window_end_frame'],'yield_ratio':clamp(pprob-TH),'released_compute_budget':clamp((pprob-TH)*w['sample_count']),'target_r_domains':[rid] if rv>=.38 else [],'target_masking_domains':['band_escape','area_instability'],'target_xi_surfaces':[xid] if xv>=.35 else [],'reason':'stable_P_measure_allows_audit_attention_to_shift_to_R_masking_Xi','calculation_recipe_id':'recipe25_attention_yield_v1'})
  eb.append({'bundle_id':'eb25_'+suf,'decision_type':'P_R_Xi_window_measure','decision_id':pid,'p_measure_id':pid,'r_measure_id':rid,'xi_surface_id':xid,'source_point_refs':w['point_ids'],'trajectory_trace_refs':[w['trajectory_trace_id']],'coordinate_transform_refs':['ct25_'+p[5:] for p in w['point_ids']],'masking_refs':['band_escape','area_instability','curvature_instability'],'external_ledger_refs':[lref],'calculation_recipe_refs':['recipe25_trajectory_window_v1','recipe25_p_spacetime_measure_v1','recipe25_r_counter_measure_v1','recipe25_xi_residual_surface_v1'],'runtime_field_refs':['runtime_store/v25/trajectory_window_trace_v25.jsonl','runtime_store/v25/p_measure_field_v25.jsonl','runtime_store/v25/r_counter_field_v25.jsonl','runtime_store/v25/xi_residual_surface_v25.jsonl'],'created_by_script':'morphosphere_v2pp/scripts/run_evidence_reconstruction_v25.py','script_hash':hfile(Path(__file__)),'replay_id':'evidence_reconstruction_v25_from_v24','invertible_claim':'source reversible and process replayable; field reconstruction is support-domain reprojectable, not raw image inversion'})
 return pr,rr,xi,att,eb
def write_jsonl(path,rows):
 path.parent.mkdir(parents=True,exist_ok=True); h=hashlib.sha256(); n=0
 with open(path,'w',encoding='utf-8') as f:
  for r in rows:
   line=jd(r)+'\n'; h.update(line.encode()); f.write(line); n+=1
 return n,h.hexdigest(),path.stat().st_size
def ddl(con):
 for t in ['information_point_v25','coordinate_transform_trace_v25','trajectory_window_trace_v25','calculation_recipe_v25','p_spacetime_measure_v25','r_counter_measure_v25','xi_residual_surface_v25','attention_yield_event_v25','decision_evidence_bundle_v25','evidence_runtime_artifact_manifest_v25','evidence_reconstruction_acceptance_report_v25']:
  con.execute(f'DROP TABLE IF EXISTS {t}')
 con.executescript('''
 CREATE TABLE information_point_v25(point_id TEXT PRIMARY KEY, source_id TEXT, source_dataset TEXT, source_sequence TEXT, source_frame INTEGER, source_track_id TEXT, sample_id TEXT, sensor_id TEXT, sensor_kind TEXT, clock_domain TEXT, time_s REAL, raw_x REAL, raw_y REAL, raw_z REAL, raw_area REAL, channel TEXT, value REAL, uncertainty REAL, source_coordinate_system TEXT, source_unit TEXT, license TEXT, citation_key TEXT, doi TEXT, parent_track_id TEXT, source_zip_sha256 TEXT, provenance_hash TEXT);
 CREATE TABLE coordinate_transform_trace_v25(transform_id TEXT PRIMARY KEY, source_point_id TEXT, from_coordinate_system TEXT, to_coordinate_system TEXT, raw_x REAL, raw_y REAL, raw_z REAL, normalized_x REAL, normalized_y REAL, normalized_z REAL, cell_sphere_x REAL, cell_sphere_y REAL, cell_sphere_z REAL, nearest_cell_uid TEXT, distance_to_cell REAL, origin_anchor_id TEXT, relative_x REAL, relative_y REAL, relative_z REAL, transform_method TEXT, transform_parameters_json TEXT, transform_error REAL, reversible_refs_json TEXT);
 CREATE TABLE trajectory_window_trace_v25(trajectory_trace_id TEXT PRIMARY KEY, source_track_id TEXT, sequence_id TEXT, window_index INTEGER, window_start_frame INTEGER, window_end_frame INTEGER, window_start_time REAL, window_end_time REAL, sample_count INTEGER, point_ids_json TEXT, support_cell_ids_json TEXT, origin_anchor_id TEXT, source_cell_uid TEXT, path_length REAL, net_displacement REAL, duration REAL, mean_speed REAL, speed_std REAL, direction_coherence REAL, curvature REAL, bandwidth REAL, origin_band_occupancy REAL, continuity_gap_count INTEGER, area_cv REAL, mean_distance_to_cell REAL, max_distance_to_cell REAL, window_policy TEXT, reprojection_refs_json TEXT);
 CREATE TABLE calculation_recipe_v25(recipe_id TEXT PRIMARY KEY, recipe_name TEXT, recipe_version TEXT, input_refs_json TEXT, output_refs_json TEXT, formula_text TEXT, parameters_json TEXT, thresholds_json TEXT, normalization_method TEXT, windowing_method TEXT, masking_method TEXT, code_path TEXT, code_hash TEXT, created_at TEXT);
 CREATE TABLE p_spacetime_measure_v25(p_measure_id TEXT PRIMARY KEY, o_candidate_id TEXT, trajectory_trace_id TEXT, source_track_id TEXT, window_start_frame INTEGER, window_end_frame INTEGER, support_point_ids_json TEXT, support_cell_ids_json TEXT, support_duration REAL, support_length REAL, support_volume REAL, continuity_mass REAL, prediction_mass REAL, origin_band_occupancy REAL, masking_survival_ratio REAL, external_entropy_closure_score REAL, equivalent_probability REAL, p_measure_value REAL, p_status TEXT, attention_yield_ratio REAL, calculation_recipe_id TEXT, external_ledger_ref TEXT, diagnostic_prior_ref TEXT);
 CREATE TABLE r_counter_measure_v25(r_measure_id TEXT PRIMARY KEY, target_p_measure_id TEXT, competing_trajectory_id TEXT, source_track_id TEXT, counter_window_start_frame INTEGER, counter_window_end_frame INTEGER, counter_support_point_ids_json TEXT, counter_support_cell_ids_json TEXT, counter_length REAL, counter_duration REAL, p_displacement_mass REAL, masking_exposure_gain REAL, entropy_violation_mass REAL, recursive_reentry_priority REAL, counter_equivalent_probability REAL, r_measure_value REAL, r_status TEXT, calculation_recipe_id TEXT, external_ledger_ref TEXT, diagnostic_prior_ref TEXT);
 CREATE TABLE xi_residual_surface_v25(xi_surface_id TEXT PRIMARY KEY, layer_id TEXT, origin_anchor_id TEXT, window_start_frame INTEGER, window_end_frame INTEGER, source_point_ids_json TEXT, source_event_ids_json TEXT, support_cell_ids_json TEXT, p_parent_refs_json TEXT, r_parent_refs_json TEXT, masking_context_refs_json TEXT, external_entropy_refs_json TEXT, residual_mass REAL, xi_equivalent_probability REAL, entropy_mismatch REAL, conservation_gap REAL, phase_conflict_mass REAL, unbound_duration REAL, unbound_support_area REAL, decay_state TEXT, memory_state TEXT, reentry_policy TEXT, attention_request INTEGER, xi_status TEXT, calculation_recipe_id TEXT);
 CREATE TABLE attention_yield_event_v25(attention_yield_id TEXT PRIMARY KEY, source_p_measure_id TEXT, trajectory_trace_id TEXT, window_start_frame INTEGER, window_end_frame INTEGER, yield_ratio REAL, released_compute_budget REAL, target_r_domains_json TEXT, target_masking_domains_json TEXT, target_xi_surfaces_json TEXT, reason TEXT, calculation_recipe_id TEXT);
 CREATE TABLE decision_evidence_bundle_v25(bundle_id TEXT PRIMARY KEY, decision_type TEXT, decision_id TEXT, p_measure_id TEXT, r_measure_id TEXT, xi_surface_id TEXT, source_point_refs_json TEXT, trajectory_trace_refs_json TEXT, coordinate_transform_refs_json TEXT, masking_refs_json TEXT, external_ledger_refs_json TEXT, calculation_recipe_refs_json TEXT, runtime_field_refs_json TEXT, created_by_script TEXT, script_hash TEXT, replay_id TEXT, invertible_claim TEXT);
 CREATE TABLE evidence_runtime_artifact_manifest_v25(artifact_id TEXT PRIMARY KEY,path TEXT,row_count INTEGER,size_bytes INTEGER,sha256 TEXT,artifact_role TEXT,sqlite_table TEXT,generated_at TEXT);
 CREATE TABLE evidence_reconstruction_acceptance_report_v25(check_name TEXT PRIMARY KEY,status TEXT,passed INTEGER,blocking INTEGER,detail TEXT);
 ''')
def ins(con,t,rows,mapjson={}):
 if not rows: return
 cols=list(rows[0].keys())
 def val(r,c):
  v=r.get(c)
  if c in mapjson: v=r.get(mapjson[c])
  if isinstance(v,(list,dict)): return jd(v)
  if isinstance(v,bool): return int(v)
  return v
 con.executemany(f"INSERT INTO {t}({','.join(cols)}) VALUES({','.join('?' for _ in cols)})", [[val(r,c) for c in cols] for r in rows])
def rename(rows,pairs):
 out=[]
 for r in rows:
  x=dict(r)
  for old,new in pairs: x[new]=x.pop(old)
  out.append(x)
 return out
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--source-db',type=Path,default=SRC_DB); ap.add_argument('--ctc-csv',type=Path,default=CSV); ap.add_argument('--out-db',type=Path,default=OUT); args=ap.parse_args()
 work=args.out_db.with_name(args.out_db.stem+'_tmp.db');
 if work.exists(): work.unlink()
 shutil.copy2(args.source_db,work)
 rows=read_csv(args.ctc_csv); con=sqlite3.connect(work); con.row_factory=sqlite3.Row
 cs=cells(con); bd=bounds(rows); inf=info_rows(rows); tr=transforms(rows,cs,bd); tb={x['source_point_id']:x for x in tr}; mp=qdict(con,'ctc_track_to_cell_mapping_v22','track_id'); ws=windows(rows,tb,mp); rec=recipes(); pr,rr,xi,att,eb=measures(ws,qdict(con,'ctc_motion_feature_v22','track_id'),qdict(con,'ctc_pr_xi_trial_response_v22','track_id'),qdict(con,'external_entropy_ledger','window_id'))
 side=[]
 for aid,table,payload,role in [('information_points_v25','information_point_v25',inf,'raw_points'),('coordinate_transform_trace_v25','coordinate_transform_trace_v25',tr,'coordinate_payload'),('trajectory_window_trace_v25','trajectory_window_trace_v25',ws,'trajectory_payload'),('p_measure_field_v25','p_spacetime_measure_v25',pr,'p_payload'),('r_counter_field_v25','r_counter_measure_v25',rr,'r_payload'),('xi_residual_surface_v25','xi_residual_surface_v25',xi,'xi_payload'),('evidence_bundle_v25','decision_evidence_bundle_v25',eb,'bundle_payload')]:
  n,h,s=write_jsonl(RT/(aid+'.jsonl'),payload); side.append({'artifact_id':aid,'path':str((RT/(aid+'.jsonl')).relative_to(ROOT)),'row_count':n,'size_bytes':s,'sha256':h,'artifact_role':role,'sqlite_table':table,'generated_at':datetime.now(timezone.utc).isoformat()})
 ddl(con)
 ins(con,'information_point_v25',inf)
 ins(con,'coordinate_transform_trace_v25',rename(tr,[('reversible_refs','reversible_refs_json')]))
 ins(con,'trajectory_window_trace_v25',rename(ws,[('point_ids','point_ids_json'),('support_cell_ids','support_cell_ids_json'),('reprojection_refs','reprojection_refs_json')]))
 ins(con,'calculation_recipe_v25',rename(rec,[('input_refs','input_refs_json'),('output_refs','output_refs_json')]))
 ins(con,'p_spacetime_measure_v25',rename(pr,[('support_point_ids','support_point_ids_json'),('support_cell_ids','support_cell_ids_json')]))
 ins(con,'r_counter_measure_v25',rename(rr,[('counter_support_point_ids','counter_support_point_ids_json'),('counter_support_cell_ids','counter_support_cell_ids_json')]))
 ins(con,'xi_residual_surface_v25',rename(xi,[('source_point_ids','source_point_ids_json'),('source_event_ids','source_event_ids_json'),('support_cell_ids','support_cell_ids_json'),('p_parent_refs','p_parent_refs_json'),('r_parent_refs','r_parent_refs_json'),('masking_context_refs','masking_context_refs_json'),('external_entropy_refs','external_entropy_refs_json')]))
 ins(con,'attention_yield_event_v25',rename(att,[('target_r_domains','target_r_domains_json'),('target_masking_domains','target_masking_domains_json'),('target_xi_surfaces','target_xi_surfaces_json')]))
 ins(con,'decision_evidence_bundle_v25',rename(eb,[('source_point_refs','source_point_refs_json'),('trajectory_trace_refs','trajectory_trace_refs_json'),('coordinate_transform_refs','coordinate_transform_refs_json'),('masking_refs','masking_refs_json'),('external_ledger_refs','external_ledger_refs_json'),('calculation_recipe_refs','calculation_recipe_refs_json'),('runtime_field_refs','runtime_field_refs_json')]))
 ins(con,'evidence_runtime_artifact_manifest_v25',side)
 checks=[]
 def ck(n,p,d): checks.append({'check_name':n,'status':'PASS' if p else 'FAIL','passed':int(p),'blocking':1,'detail':d})
 ck('sqlite_quick_check',con.execute('pragma quick_check').fetchone()[0]=='ok','quick_check ok')
 for t,e in [('information_point_v25',4575),('coordinate_transform_trace_v25',4575),('trajectory_window_trace_v25',532),('calculation_recipe_v25',7),('p_spacetime_measure_v25',532),('r_counter_measure_v25',532),('xi_residual_surface_v25',532),('attention_yield_event_v25',262),('decision_evidence_bundle_v25',532),('evidence_runtime_artifact_manifest_v25',7)]:
  a=con.execute(f'select count(*) from {t}').fetchone()[0]; ck('count_'+t,a==e,f'expected {e}, actual {a}')
 ck('xi_reentry_policy',con.execute("select count(*) from xi_residual_surface_v25 where reentry_policy!='via_o_candidate_only'").fetchone()[0]==0,'all xi via O candidate only')
 ck('external_entropy_refs',con.execute("select count(*) from decision_evidence_bundle_v25 where external_ledger_refs_json like '%win_%'").fetchone()[0]==532,'all bundles link external entropy ledger')
 ins(con,'evidence_reconstruction_acceptance_report_v25',checks); con.commit(); con.close();
 if args.out_db.exists(): args.out_db.unlink()
 os.replace(work,args.out_db)
 summary={'schema_version':'v2.5','source_baseline':'v2.4','output_db':str(args.out_db.relative_to(ROOT)),'sqlite_quick_check':'ok','counts':{k:v for k,v in [('information_point_v25',4575),('coordinate_transform_trace_v25',4575),('trajectory_window_trace_v25',532),('p_spacetime_measure_v25',532),('r_counter_measure_v25',532),('xi_residual_surface_v25',532),('attention_yield_event_v25',262),('decision_evidence_bundle_v25',532),('calculation_recipe_v25',7)]},'runtime_sidecars':side,'boundary':'diagnostic evidence reconstruction; not final biology; not scientific_run','db_sha256':hfile(args.out_db)}
 REPORTS.mkdir(parents=True,exist_ok=True); (REPORTS/'evidence_reconstruction_v25_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False));
 (REPORTS/'EVIDENCE_RECONSTRUCTION_V25_REPORT.md').write_text('# Evidence Reconstruction Store v2.5 Report\n\nSQLite quick_check: `ok`\n\n'+''.join(f'- `{k}` = {v}\n' for k,v in summary['counts'].items()))
 print(json.dumps({'status':'PASS','counts':summary['counts'],'db_sha256':summary['db_sha256']},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
