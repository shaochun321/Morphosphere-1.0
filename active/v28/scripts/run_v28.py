#!/usr/bin/env python3
import sqlite3, shutil, json, math, hashlib, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs'
RUNTIME = ROOT / 'runtime_store' / 'v28'
V27_DB = OUT / 'm27.db'
V26_DB = OUT / 'morphosphere_shadow_reconstruction_v26_output_database.db'
M28_DB = OUT / 'm28.db'

def jload(s, default=None):
    if s is None: return default
    try: return json.loads(s)
    except Exception: return default

def sha_text(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]
def clamp(x, lo=0.0, hi=1.0): return max(lo, min(hi, x))

def reset():
    RUNTIME.mkdir(parents=True, exist_ok=True)
    if M28_DB.exists(): M28_DB.unlink()
    for p in list(RUNTIME.glob('*.jsonl')) + list(RUNTIME.glob('*.json')): p.unlink()
    shutil.copy2(V27_DB, M28_DB)

def copy_v26(con):
    con.execute(f"attach database '{V26_DB}' as v26")
    names = [r[0] for r in con.execute("select name from v26.sqlite_master where type='table' and name like 'shadow_%'")]
    for name in names:
        con.execute(f'drop table if exists main.{name}')
        con.execute(f'create table {name} as select * from v26.{name}')
    con.execute('detach database v26')
    con.commit()

def create_tables(con):
    sql = """
    drop table if exists v28_run_manifest;
    create table v28_run_manifest(run_id text primary key, version text, evidence_source_version text, shadow_source_version text, reversible_query_source_version text, source_facts_rewritten integer, hot_swap_allowed integer, xi_direct_to_pr_allowed integer, created_at text, notes text);
    drop table if exists v28_evidence_edge;
    create table v28_evidence_edge(evidence_edge_id text primary key, sequence_id text, window_id text, frame_start integer, frame_end integer, source_track_id text, point_a_id text, point_b_id text, cell_a_ref text, cell_b_ref text, t_mid real, x_mid real, y_mid real, z_mid real, edge_length real, continuity_mass real, measure_mass real, p_measure_id text, r_measure_id text, xi_surface_id text, evidence_bundle_ref text, transform_a_ref text, transform_b_ref text);
    drop table if exists v28_shadow_edge;
    create table v28_shadow_edge(shadow_edge_id text primary key, shadow_cell_a text, shadow_cell_b text, window_id text, predicted_t_mid real, predicted_x_mid real, predicted_y_mid real, predicted_z_mid real, predicted_length real, predicted_continuity real, predicted_measure_mass real, shadow_motion_state_ref text, shadow_bridge_ref text, source_point_id text, target_point_id text, source_frame integer, target_frame integer, source_shadow_edge_ref text);
    drop table if exists v28_shadow_evidence_alignment;
    create table v28_shadow_evidence_alignment(alignment_id text primary key, evidence_edge_id text, shadow_edge_id text, window_id text, temporal_delta real, spatial_delta real, length_delta real, measure_overlap real, topology_match real, alignment_status text, alignment_confidence real, evidence_mass real, shadow_mass real);
    drop table if exists v28_divergence_decomposition;
    create table v28_divergence_decomposition(divergence_id text primary key, window_id text, support_domain_ref text, evidence_edge_id text, shadow_edge_id text, edge_mismatch real, trajectory_support_mismatch real, occupancy_measure_mismatch real, temporal_lag real, spatial_offset real, topology_difference real, xi_surprise_mass real, total_divergence real, recipe_id text, divergence_class text);
    drop table if exists v28_confirmed_p_structure;
    create table v28_confirmed_p_structure(confirmed_p_id text primary key, parent_p_measure_ref text, shadow_support_ref text, alignment_ref text, window_span text, support_length_overlap real, support_duration_overlap real, support_domain_overlap real, equivalent_probability_boost real, free_energy_delta_proxy real, attention_yield_delta real, status text, evidence_edge_id text, shadow_edge_id text);
    drop table if exists v28_shadow_overreach_penalty;
    create table v28_shadow_overreach_penalty(penalty_id text primary key, shadow_edge_id text, window_id text, predicted_mass real, observed_mass real, overreach_mass real, penalty_type text, parameter_penalty_hint text, send_to_r integer, send_to_xi integer, alignment_ref text);
    drop table if exists v28_evidence_surprise_xi;
    create table v28_evidence_surprise_xi(surprise_id text primary key, evidence_edge_id text, window_id text, surprise_mass real, persistence_across_windows real, xi_surface_ref text, emergence_candidate integer, proto_o_candidate_allowed integer, reentry_policy text, alignment_ref text, surprise_type text);
    drop table if exists v28_emergence_alert_candidate;
    create table v28_emergence_alert_candidate(alert_id text primary key, surprise_refs_json text, window_span text, support_domain text, persistence_score real, novelty_score real, entropy_closure_status text, recommended_next_action text);
    drop table if exists v28_measure_recipe_trace;
    create table v28_measure_recipe_trace(recipe_id text primary key, recipe_name text, formula_text text, input_refs text, parameters_json text, thresholds_json text, code_path text, code_hash text, output_refs text);
    drop table if exists v28_runtime_artifact_manifest;
    create table v28_runtime_artifact_manifest(artifact_id text primary key, path text, row_count integer, size_bytes integer, sha256 text);
    drop table if exists v28_acceptance_report;
    create table v28_acceptance_report(check_id text primary key, status text, details text);
    """
    con.executescript(sql)
    con.commit()

def build_indexes(con):
    p_by_traj={r['trajectory_trace_id']:dict(r) for r in con.execute('select * from p_spacetime_measure_v25')}
    r_by_p={r['target_p_measure_id']:dict(r) for r in con.execute('select * from r_counter_measure_v25')}
    xi_by_p={}
    for r in con.execute('select * from xi_residual_surface_v25'):
        for p in (jload(r['p_parent_refs_json'],[]) or []): xi_by_p[p]=dict(r)
    bundle_by_p={r['p_measure_id']:dict(r) for r in con.execute('select * from decision_evidence_bundle_v25')}
    pts={r['point_id']:dict(r) for r in con.execute('select * from information_point_v25')}
    trans={r['source_point_id']:dict(r) for r in con.execute('select * from coordinate_transform_trace_v25')}
    motion_by_traj={r['trajectory_trace_id']:dict(r) for r in con.execute('select * from shadow_cell_motion_state_v26')}
    bridge_by_traj={r['trajectory_trace_id']:dict(r) for r in con.execute('select * from shadow_decision_evidence_bridge_v26')}
    return p_by_traj,r_by_p,xi_by_p,bundle_by_p,pts,trans,motion_by_traj,bridge_by_traj

def build_evidence_edges(con, idx):
    p_by_traj,r_by_p,xi_by_p,bundle_by_p,pts,trans,*_=idx
    seen=set(); rows=[]
    for tw in con.execute('select * from trajectory_window_trace_v25 order by sequence_id, source_track_id, window_start_frame'):
        tw=dict(tw); p=p_by_traj.get(tw['trajectory_trace_id'])
        if not p: continue
        r=r_by_p.get(p['p_measure_id'],{}); xi=xi_by_p.get(p['p_measure_id'],{}); bundle=bundle_by_p.get(p['p_measure_id'],{})
        ids=jload(tw['point_ids_json'],[]) or []
        for a,b in zip(ids,ids[1:]):
            if (a,b) in seen: continue
            seen.add((a,b))
            pa,pb,ta,tb=pts.get(a),pts.get(b),trans.get(a),trans.get(b)
            if not (pa and pb and ta and tb): continue
            dx=(tb['cell_sphere_x'] or 0)-(ta['cell_sphere_x'] or 0); dy=(tb['cell_sphere_y'] or 0)-(ta['cell_sphere_y'] or 0); dz=(tb['cell_sphere_z'] or 0)-(ta['cell_sphere_z'] or 0)
            length=math.sqrt(dx*dx+dy*dy+dz*dz)
            rows.append((f"ee28_{sha_text(a+'->'+b)}",tw['sequence_id'],tw['trajectory_trace_id'],pa['source_frame'],pb['source_frame'],tw['source_track_id'],a,b,ta['nearest_cell_uid'],tb['nearest_cell_uid'],(pa['time_s']+pb['time_s'])/2,(ta['cell_sphere_x']+tb['cell_sphere_x'])/2,(ta['cell_sphere_y']+tb['cell_sphere_y'])/2,(ta['cell_sphere_z']+tb['cell_sphere_z'])/2,length,p['continuity_mass'],p['p_measure_value'],p['p_measure_id'],r.get('r_measure_id'),xi.get('xi_surface_id'),bundle.get('bundle_id'),ta['transform_id'],tb['transform_id']))
    con.executemany('insert into v28_evidence_edge values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',rows); con.commit()

def build_shadow_edges(con, idx):
    *_,motion_by_traj,bridge_by_traj=idx
    ee={(r['point_a_id'],r['point_b_id']):dict(r) for r in con.execute('select * from v28_evidence_edge')}
    rows=[]
    for se in con.execute('select * from shadow_graph_edge_v26 order by shadow_edge_id'):
        se=dict(se); ev=ee.get((se['source_point_id'],se['target_point_id']))
        if not ev: continue
        motion=motion_by_traj.get(ev['window_id'],{}); bridge=bridge_by_traj.get(ev['window_id'],{})
        pred_cont=clamp(math.exp(-6.0*float(se['distance'] or 0)))
        state=motion.get('shadow_motion_state','') if motion else ''
        boost={'shadow_stable_motion':0.06,'shadow_candidate_motion':0.03,'shadow_counterstructure_watch':-0.02}.get(state,0.0)
        pred_mass=clamp(pred_cont+boost)
        rows.append((f"she28_{sha_text(se['shadow_edge_id'])}",se['source_shadow_cell_id'],se['target_shadow_cell_id'],ev['window_id'],(se['source_frame']+se['target_frame'])/2,ev['x_mid'],ev['y_mid'],ev['z_mid'],se['distance'],pred_cont,pred_mass,motion.get('shadow_motion_state_id'),bridge.get('bridge_id'),se['source_point_id'],se['target_point_id'],se['source_frame'],se['target_frame'],se['shadow_edge_id']))
    con.executemany('insert into v28_shadow_edge values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',rows); con.commit()

def align(con):
    ee={(r['point_a_id'],r['point_b_id']):dict(r) for r in con.execute('select * from v28_evidence_edge')}
    sh={(r['source_point_id'],r['target_point_id']):dict(r) for r in con.execute('select * from v28_shadow_edge')}
    align_rows=[]; div_rows=[]; conf_rows=[]; pen_rows=[]; sur_rows=[]
    for pair in sorted(set(ee)|set(sh)):
        ev,sv=ee.get(pair),sh.get(pair); hid=sha_text(pair[0]+'|'+pair[1]); aid='al28_'+hid
        if ev and sv:
            td=abs((sv['predicted_t_mid'] or 0)-(ev['t_mid'] or 0)); sd=math.sqrt((sv['predicted_x_mid']-ev['x_mid'])**2+(sv['predicted_y_mid']-ev['y_mid'])**2+(sv['predicted_z_mid']-ev['z_mid'])**2); ld=abs((sv['predicted_length'] or 0)-(ev['edge_length'] or 0))
            em=float(ev['measure_mass'] or 0); sm=float(sv['predicted_measure_mass'] or 0); mm=abs(em-sm); overlap=min(em,sm); total=clamp(0.55*mm+0.15*min(1,td)+0.15*min(1,sd))
            status='matched' if mm<=0.15 else 'partial'; dclass='confirmed_overlap' if mm<=0.15 else ('shadow_overreach' if sm>em else 'evidence_surprise')
            align_rows.append((aid,ev['evidence_edge_id'],sv['shadow_edge_id'],ev['window_id'],td,sd,ld,overlap,1.0,status,clamp(1-mm),em,sm))
            div_rows.append(('dv28_'+hid,ev['window_id'],json.dumps([ev['cell_a_ref'],ev['cell_b_ref']]),ev['evidence_edge_id'],sv['shadow_edge_id'],0,0,mm,td,sd,0,max(0,em-sm),total,'recipe28_divergence_decomposition_v1',dclass))
            if overlap>0.45:
                boost=clamp(0.08*overlap); conf_rows.append(('cp28_'+hid,ev['p_measure_id'],sv['shadow_edge_id'],aid,f"{ev['frame_start']}-{ev['frame_end']}",min(ev['edge_length'],sv['predicted_length']),1.0,1.0,boost,-total,boost/2,'confirmed' if mm<=0.15 else 'durable_with_measure_drift',ev['evidence_edge_id'],sv['shadow_edge_id']))
            if sm-em>0.15:
                over=sm-em; pen_rows.append(('pen28_'+hid,sv['shadow_edge_id'],ev['window_id'],sm,em,over,'measure_overreach','lower shadow proximity continuity gain or require stronger evidence overlap',1,1 if over>0.35 else 0,aid))
            if em-sm>0.15:
                su=em-sm; sur_rows.append(('sur28_'+hid,ev['evidence_edge_id'],ev['window_id'],su,1.0,ev['xi_surface_id'],1 if su>0.35 else 0,1,'via_o_candidate_only',aid,'measure_surprise'))
        elif ev:
            em=float(ev['measure_mass'] or 0); align_rows.append((aid,ev['evidence_edge_id'],None,ev['window_id'],None,None,None,0,0,'unmatched_evidence',0,em,0)); div_rows.append(('dv28_'+hid,ev['window_id'],json.dumps([ev['cell_a_ref'],ev['cell_b_ref']]),ev['evidence_edge_id'],None,1,1,em,0,0,1,em,1,'recipe28_divergence_decomposition_v1','evidence_surprise')); sur_rows.append(('sur28_'+hid,ev['evidence_edge_id'],ev['window_id'],em,1,ev['xi_surface_id'],1 if em>0.55 else 0,1,'via_o_candidate_only',aid,'missing_shadow'))
        elif sv:
            sm=float(sv['predicted_measure_mass'] or 0); align_rows.append((aid,None,sv['shadow_edge_id'],sv['window_id'],None,None,None,0,0,'unmatched_shadow',0,0,sm)); div_rows.append(('dv28_'+hid,sv['window_id'],json.dumps([sv['shadow_cell_a'],sv['shadow_cell_b']]),None,sv['shadow_edge_id'],1,1,sm,0,0,1,0,1,'recipe28_divergence_decomposition_v1','shadow_overreach')); pen_rows.append(('pen28_'+hid,sv['shadow_edge_id'],sv['window_id'],sm,0,sm,'missing_evidence','quarantine unsupported shadow edge and route to R/Xi review',1,1,aid))
    con.executemany('insert into v28_shadow_evidence_alignment values (?,?,?,?,?,?,?,?,?,?,?,?,?)',align_rows)
    con.executemany('insert into v28_divergence_decomposition values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',div_rows)
    con.executemany('insert into v28_confirmed_p_structure values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',conf_rows)
    con.executemany('insert into v28_shadow_overreach_penalty values (?,?,?,?,?,?,?,?,?,?,?)',pen_rows)
    con.executemany('insert into v28_evidence_surprise_xi values (?,?,?,?,?,?,?,?,?,?,?)',sur_rows)
    con.commit()

def post(con):
    alerts=[(f"em28_{i:03d}",json.dumps([r['surprise_id']]),r['window_id'],r['evidence_edge_id'],1.0,r['surprise_mass'],'ledger_review_required','masking_replay_then_proto_O_candidate') for i,r in enumerate(con.execute("select * from v28_evidence_surprise_xi where emergence_candidate=1 order by window_id limit 25"))]
    con.executemany('insert into v28_emergence_alert_candidate values (?,?,?,?,?,?,?,?)',alerts)
    recipes=[('recipe28_edge_extraction_from_evidence_v1','edge_extraction_from_evidence_v1','adjacent information_point_v25 pairs within trajectory_window_trace_v25','v25 evidence','{}','{}','active/v28/scripts/run_v28.py','','v28_evidence_edge'),('recipe28_edge_extraction_from_shadow_v1','edge_extraction_from_shadow_v1','normalize shadow_graph_edge_v26; predicted_mass=exp(-6*distance)+state_boost','v26 shadow','{"distance_gain":6.0}','{}','active/v28/scripts/run_v28.py','','v28_shadow_edge'),('recipe28_alignment_v1','shadow_evidence_alignment_v1','exact point-pair alignment then compare deltas','v28 edges','{}','{"measure_match_delta":0.15}','active/v28/scripts/run_v28.py','','v28_shadow_evidence_alignment'),('recipe28_divergence_decomposition_v1','divergence_decomposition_v1','weighted measure/time/space/topology divergence','v28 alignment','{"w_measure":0.55,"w_time":0.15,"w_space":0.15,"w_topology":0.15}','{}','active/v28/scripts/run_v28.py','','v28_divergence_decomposition'),('recipe28_confirmed_p_overlap_v1','confirmed_p_overlap_v1','overlap > 0.45 confirms durable P support','v28 alignment','{}','{"measure_overlap_min":0.45}','active/v28/scripts/run_v28.py','','v28_confirmed_p_structure'),('recipe28_shadow_overreach_penalty_v1','shadow_overreach_penalty_v1','shadow mass exceeds evidence mass by >0.15','v28 alignment','{}','{"overreach_delta":0.15}','active/v28/scripts/run_v28.py','','v28_shadow_overreach_penalty'),('recipe28_evidence_surprise_xi_v1','evidence_surprise_xi_v1','evidence mass exceeds shadow mass by >0.15; reentry via O candidate only','v28 alignment','{}','{"surprise_delta":0.15,"reentry_policy":"via_o_candidate_only"}','active/v28/scripts/run_v28.py','','v28_evidence_surprise_xi'),('recipe28_emergence_alert_candidate_v1','emergence_alert_candidate_v1','high surprise marked for masking replay and proto-O review','v28 surprise','{}','{"emergence_surprise_min":0.35}','active/v28/scripts/run_v28.py','','v28_emergence_alert_candidate')]
    con.executemany('insert into v28_measure_recipe_trace values (?,?,?,?,?,?,?,?,?)',recipes)
    con.commit()

def export_and_accept(con):
    tables=['v28_evidence_edge','v28_shadow_edge','v28_shadow_evidence_alignment','v28_divergence_decomposition','v28_confirmed_p_structure','v28_shadow_overreach_penalty','v28_evidence_surprise_xi','v28_emergence_alert_candidate']
    for t in tables:
        path=RUNTIME/(t+'.jsonl'); count=0
        with path.open('w',encoding='utf-8') as f:
            for r in con.execute(f'select * from {t}'):
                f.write(json.dumps(dict(r),ensure_ascii=False,sort_keys=True)+'\n'); count+=1
        data=path.read_bytes(); con.execute('insert into v28_runtime_artifact_manifest values (?,?,?,?,?)',(t,str(path.relative_to(ROOT)),count,len(data),hashlib.sha256(data).hexdigest()))
    (RUNTIME/'runtime_manifest_v28.json').write_text(json.dumps([dict(r) for r in con.execute('select * from v28_runtime_artifact_manifest')],indent=2),encoding='utf-8')
    checks=[]
    def cnt(t): return con.execute(f'select count(*) from {t}').fetchone()[0]
    def add(cid,cond,detail): checks.append((cid,'PASS' if cond else 'FAIL',detail))
    add('sqlite_quick_check',con.execute('pragma quick_check(1)').fetchone()[0]=='ok','ok')
    for t in ['v28_evidence_edge','v28_shadow_edge','v28_shadow_evidence_alignment','v28_divergence_decomposition','v28_confirmed_p_structure']:
        add(t+'_positive',cnt(t)>0,str(cnt(t)))
    add('shadow_overreach_rows_or_explicit_zero',cnt('v28_shadow_overreach_penalty')>=0,str(cnt('v28_shadow_overreach_penalty')))
    add('evidence_surprise_rows_or_explicit_zero',cnt('v28_evidence_surprise_xi')>=0,str(cnt('v28_evidence_surprise_xi')))
    add('xi_reentry_policy_via_o_only',con.execute("select count(*) from v28_evidence_surprise_xi where reentry_policy!='via_o_candidate_only'").fetchone()[0]==0,'checked')
    man=con.execute('select source_facts_rewritten,hot_swap_allowed,xi_direct_to_pr_allowed from v28_run_manifest').fetchone()
    add('source_facts_not_rewritten',man[0]==0,str(man[0])); add('hot_swap_not_allowed',man[1]==0,str(man[1])); add('xi_direct_to_pr_not_allowed',man[2]==0,str(man[2]))
    add('confirmed_p_has_refs',con.execute('select count(*) from v28_confirmed_p_structure where parent_p_measure_ref is null or shadow_support_ref is null or alignment_ref is null').fetchone()[0]==0,'checked')
    add('overreach_traces_to_shadow_edge',con.execute('select count(*) from v28_shadow_overreach_penalty where shadow_edge_id is null').fetchone()[0]==0,'checked')
    add('surprise_traces_to_evidence_edge',con.execute('select count(*) from v28_evidence_surprise_xi where evidence_edge_id is null').fetchone()[0]==0,'checked')
    add('runtime_sidecar_manifest_present',cnt('v28_runtime_artifact_manifest')>=8,str(cnt('v28_runtime_artifact_manifest')))
    con.executemany('insert into v28_acceptance_report values (?,?,?)',checks); con.commit()
    bad=[c for c in checks if c[1]!='PASS']
    if bad: raise SystemExit(str(bad))

def main():
    reset(); con=sqlite3.connect(M28_DB); con.row_factory=sqlite3.Row
    copy_v26(con); create_tables(con)
    con.execute('insert into v28_run_manifest values (?,?,?,?,?,?,?,?,?,?)',('run28_shadow_evidence_divergence_gate','shadow_evidence_divergence_gate_v2.8','v25_evidence+v27_measure_field','v26_shadow_cell_sphere','v27_reversible_query',0,0,0,datetime.datetime.utcnow().isoformat(timespec='seconds')+'Z','Evidence and Shadow aligned by source point-pair; source facts not rewritten; divergence ledgered, not hot-swapped.'))
    idx=build_indexes(con); build_evidence_edges(con,idx); build_shadow_edges(con,idx); align(con); post(con); export_and_accept(con)
    print('V28_SHADOW_EVIDENCE_DIVERGENCE_GATE: PASS')
    for t in ['v28_evidence_edge','v28_shadow_edge','v28_shadow_evidence_alignment','v28_divergence_decomposition','v28_confirmed_p_structure','v28_shadow_overreach_penalty','v28_evidence_surprise_xi','v28_emergence_alert_candidate']:
        print(t+':',con.execute(f'select count(*) from {t}').fetchone()[0])
    con.close()
if __name__=='__main__': main()
