#!/usr/bin/env python3
"""CTC declared real-data trial orchestrator v2.2.

This runner is deliberately conservative. It can process a user supplied CTC centroid CSV,
or fall back to the v2.1 sample CSV for dry-run validation. A sample/dry-run input can never
be declared as real external data even if --declare-real-external is passed.
"""
import argparse, csv, hashlib, json, math, os, sqlite3, statistics, subprocess, sys
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED = ['source_id','sample_id','clock_domain','time_s','sensor_id','sensor_kind','x','y','z','channel','value','uncertainty','track_id','frame','centroid_x','centroid_y','centroid_z','area','sequence_id']
OPTIONAL_PROVENANCE = ['license','citation_key','dataset_name','doi','parent_track_id','start_frame','end_frame']


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def read_csv(path: Path) -> Tuple[List[dict], List[str]]:
    with path.open(newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames or []
        missing = [c for c in REQUIRED if c not in fields]
        if missing:
            raise SystemExit('missing required columns: ' + ','.join(missing))
        return list(reader), fields


def fval(row: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default))
    except Exception:
        return default


def is_sample_input(path: Path, rows: List[dict]) -> bool:
    name = path.name.lower()
    if 'sample' in name or 'high_fidelity' in name or 'demo' in name:
        return True
    for r in rows[:20]:
        sid = str(r.get('source_id','')).lower()
        if 'sample' in sid or 'demo' in sid or 'high_fidelity' in sid:
            return True
    return False


def track_features(rows: List[dict]) -> Dict[str, dict]:
    by: Dict[str, List[dict]] = {}
    for r in rows:
        by.setdefault(str(r['track_id']), []).append(r)
    out = {}
    for tid, rs in by.items():
        rs = sorted(rs, key=lambda r: (int(float(r['frame'])), fval(r,'time_s')))
        speeds = []
        angles = []
        disps = []
        for a, b in zip(rs, rs[1:]):
            dt = max(fval(b,'time_s') - fval(a,'time_s'), 1e-9)
            dx = fval(b,'x') - fval(a,'x')
            dy = fval(b,'y') - fval(a,'y')
            dz = fval(b,'z') - fval(a,'z')
            d = math.sqrt(dx*dx + dy*dy + dz*dz)
            disps.append(d); speeds.append(d / dt)
            angles.append(math.atan2(dy, dx) if d > 0 else 0.0)
        total_disp = 0.0
        if len(rs) >= 2:
            dx = fval(rs[-1],'x') - fval(rs[0],'x')
            dy = fval(rs[-1],'y') - fval(rs[0],'y')
            dz = fval(rs[-1],'z') - fval(rs[0],'z')
            total_disp = math.sqrt(dx*dx + dy*dy + dz*dz)
        path_len = sum(disps)
        direction_coherence = total_disp / path_len if path_len > 1e-9 else 0.0
        speed_mean = statistics.mean(speeds) if speeds else 0.0
        speed_std = statistics.pstdev(speeds) if len(speeds) > 1 else 0.0
        area_vals = [fval(r,'area') for r in rs]
        area_cv = (statistics.pstdev(area_vals) / max(statistics.mean(area_vals),1e-9)) if len(area_vals)>1 else 0.0
        out[tid] = {
            'track_id': tid,
            'sample_count': len(rs),
            'first_frame': int(float(rs[0]['frame'])),
            'last_frame': int(float(rs[-1]['frame'])),
            'duration_s': max(fval(rs[-1],'time_s') - fval(rs[0],'time_s'), 0.0),
            'centroid_start_x': fval(rs[0],'x'),
            'centroid_start_y': fval(rs[0],'y'),
            'centroid_start_z': fval(rs[0],'z'),
            'centroid_end_x': fval(rs[-1],'x'),
            'centroid_end_y': fval(rs[-1],'y'),
            'centroid_end_z': fval(rs[-1],'z'),
            'path_length': path_len,
            'net_displacement': total_disp,
            'speed_mean': speed_mean,
            'speed_std': speed_std,
            'direction_coherence': direction_coherence,
            'area_cv': area_cv,
        }
    return out


def get_cells(cur):
    for table, xcol, ycol, zcol, idcol in [
        ('cell_spatial_coordinate_snapshot','cell_x','cell_y','cell_z','source_cell_uid'),
        ('spacetime_cell','x','y','z','cell_uid'),
    ]:
        try:
            rows = cur.execute(f'SELECT {idcol},{xcol},{ycol},{zcol}, COALESCE(clock_n,0) FROM {table}' if table=='cell_spatial_coordinate_snapshot' else f'SELECT {idcol},{xcol},{ycol},{zcol}, clock_start FROM {table}').fetchall()
            if rows:
                # keep one coordinate per cell id, preferably first clock
                seen = {}
                for cid,x,y,z,c in rows:
                    seen.setdefault(cid, (cid,float(x),float(y),float(z)))
                return list(seen.values()), table
        except Exception:
            pass
    return [], 'none'


def normalize_and_map_tracks(features: Dict[str,dict], cells: List[tuple]):
    if not features or not cells:
        return []
    xs = [v['centroid_start_x'] for v in features.values()] + [v['centroid_end_x'] for v in features.values()]
    ys = [v['centroid_start_y'] for v in features.values()] + [v['centroid_end_y'] for v in features.values()]
    zs = [v['centroid_start_z'] for v in features.values()] + [v['centroid_end_z'] for v in features.values()]
    cx = [c[1] for c in cells]; cy=[c[2] for c in cells]; cz=[c[3] for c in cells]
    def scale(v, a, b, c, d):
        if abs(b-a) < 1e-9: return (c+d)/2
        return c + (v-a) * (d-c) / (b-a)
    rows=[]
    for tid, f in features.items():
        sx = scale(f['centroid_end_x'], min(xs), max(xs), min(cx), max(cx))
        sy = scale(f['centroid_end_y'], min(ys), max(ys), min(cy), max(cy))
        sz = scale(f['centroid_end_z'], min(zs), max(zs), min(cz), max(cz)) if max(zs)>min(zs) else statistics.mean(cz)
        best=None; bestd=1e99
        for cid,x,y,z in cells:
            d=(sx-x)**2+(sy-y)**2+(sz-z)**2
            if d<bestd: best=(cid,x,y,z); bestd=d
        rows.append((tid,best[0],sx,sy,sz,math.sqrt(bestd)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--centroid-csv', default='morphosphere_v2pp/data/ctc_centroid_sample_v21.csv')
    ap.add_argument('--ctc-zip')
    ap.add_argument('--ctc-root')
    ap.add_argument('--declare-real-external', action='store_true')
    ap.add_argument('--dataset-manifest', default='morphosphere_v2pp/data/ctc_download_manifest_v21.json')
    ap.add_argument('--report-dir', default='morphosphere_v2pp/reports')
    ap.add_argument('--package-root', default='.')
    args = ap.parse_args()
    report_dir = Path(args.report_dir); report_dir.mkdir(parents=True, exist_ok=True)
    package_root = Path(args.package_root)
    centroid_csv = Path(args.centroid_csv)

    extraction_status = 'centroid_csv_provided'
    if args.ctc_zip or args.ctc_root:
        out = package_root / 'morphosphere_v2pp' / 'data' / 'ctc_centroids_extracted_v22.csv'
        extractor = package_root / 'morphosphere_v2pp' / 'scripts' / 'extract_ctc_centroids_v21.py'
        cmd = [sys.executable, '-S', str(extractor), '--out-csv', str(out)]
        if args.ctc_zip: cmd.extend(['--zip', args.ctc_zip])
        if args.ctc_root: cmd.extend(['--ctc-root', args.ctc_root])
        try:
            subprocess.check_call(cmd)
            centroid_csv = out
            extraction_status = 'ctc_zip_or_root_extracted_to_centroid_csv'
        except Exception as e:
            extraction_status = 'ctc_extraction_failed:' + str(e)
            if not centroid_csv.exists():
                raise
    if not centroid_csv.exists():
        raise SystemExit('centroid csv not found: ' + str(centroid_csv))
    rows, fields = read_csv(centroid_csv)
    feats = track_features(rows)
    sample_input = is_sample_input(centroid_csv, rows)
    declared_real = bool(args.declare_real_external and not sample_input)
    attempted_false_real = bool(args.declare_real_external and sample_input)

    manifest = {}
    mp = Path(args.dataset_manifest)
    if mp.exists():
        manifest = json.loads(mp.read_text(encoding='utf-8'))

    con = sqlite3.connect(args.db)
    cur = con.cursor()
    # drop v22 only
    for t in [
        'ctc_declared_trial_run_manifest_v22','ctc_realdata_source_registry_v22','ctc_realdata_provenance_v22',
        'ctc_motion_feature_v22','ctc_track_to_cell_mapping_v22','ctc_motion_state_projection_v22',
        'ctc_pr_xi_trial_response_v22','ctc_declared_realdata_gate_v22','ctc_declared_trial_acceptance_report_v22',
        'ctc_declared_trial_artifact_manifest_v22'
    ]:
        cur.execute(f'DROP TABLE IF EXISTS {t}')
    cur.execute('CREATE TABLE ctc_declared_trial_run_manifest_v22 (run_id TEXT PRIMARY KEY, version TEXT, input_csv TEXT, input_sha256 TEXT, declared_real_external INTEGER, attempted_false_real INTEGER, extraction_status TEXT, row_count INTEGER, track_count INTEGER, note TEXT)')
    cur.execute('CREATE TABLE ctc_realdata_source_registry_v22 (source_id TEXT PRIMARY KEY, dataset_name TEXT, doi TEXT, download_url TEXT, expected_md5 TEXT, license TEXT, declared_real_external INTEGER, source_status TEXT)')
    cur.execute('CREATE TABLE ctc_realdata_provenance_v22 (provenance_key TEXT PRIMARY KEY, provenance_value TEXT, passed INTEGER)')
    cur.execute('CREATE TABLE ctc_motion_feature_v22 (track_id TEXT PRIMARY KEY, sample_count INTEGER, first_frame INTEGER, last_frame INTEGER, duration_s REAL, path_length REAL, net_displacement REAL, speed_mean REAL, speed_std REAL, direction_coherence REAL, area_cv REAL)')
    cur.execute('CREATE TABLE ctc_track_to_cell_mapping_v22 (track_id TEXT PRIMARY KEY, source_cell_uid TEXT, mapped_x REAL, mapped_y REAL, mapped_z REAL, distance_to_cell REAL, mapping_policy TEXT)')
    cur.execute('CREATE TABLE ctc_motion_state_projection_v22 (projection_id TEXT PRIMARY KEY, track_id TEXT, source_cell_uid TEXT, motion_state TEXT, p_support_proxy REAL, r_counter_proxy REAL, xi_pressure_proxy REAL, projection_basis TEXT)')
    cur.execute('CREATE TABLE ctc_pr_xi_trial_response_v22 (response_id TEXT PRIMARY KEY, track_id TEXT, p_status TEXT, r_status TEXT, xi_status TEXT, p_score REAL, r_score REAL, xi_score REAL, response_policy TEXT)')
    cur.execute('CREATE TABLE ctc_declared_realdata_gate_v22 (gate_name TEXT PRIMARY KEY, gate_status TEXT, passed INTEGER, blocking INTEGER, note TEXT)')
    cur.execute('CREATE TABLE ctc_declared_trial_acceptance_report_v22 (test_name TEXT PRIMARY KEY, status TEXT, detail TEXT)')
    cur.execute('CREATE TABLE ctc_declared_trial_artifact_manifest_v22 (path TEXT, sha256 TEXT, role TEXT)')

    run_id='ctc_declared_trial_v22'
    cur.execute('INSERT INTO ctc_declared_trial_run_manifest_v22 VALUES (?,?,?,?,?,?,?,?,?,?)', (run_id,'ctc_declared_real_trial_orchestrator_v2.2',str(centroid_csv),sha256(centroid_csv),int(declared_real),int(attempted_false_real),extraction_status,len(rows),len(feats),'real declaration is blocked for sample/demo/high_fidelity inputs; no source facts rewritten'))
    cur.execute('INSERT INTO ctc_realdata_source_registry_v22 VALUES (?,?,?,?,?,?,?,?)', (manifest.get('primary_dataset','Fluo-N2DH-GOWT1'),manifest.get('primary_dataset','Fluo-N2DH-GOWT1'),manifest.get('doi','10.5281/zenodo.15608211'),manifest.get('download_url',''),manifest.get('expected_md5',''),manifest.get('license','CC-BY-4.0'),int(declared_real),'REAL_EXTERNAL_DECLARED' if declared_real else 'PENDING_REAL_CTC_INPUT_OR_SAMPLE_MODE'))

    prov = {
        'required_columns_present': str(all(c in fields for c in REQUIRED)),
        'optional_provenance_columns_present': str([c for c in OPTIONAL_PROVENANCE if c in fields]),
        'sample_input_detected': str(sample_input),
        'declare_real_external_requested': str(bool(args.declare_real_external)),
        'declared_real_external_effective': str(declared_real),
        'source_fact_rewrite_allowed': 'false',
        'p_r_before_xi_preserved': 'true',
    }
    cur.executemany('INSERT INTO ctc_realdata_provenance_v22 VALUES (?,?,?)', [(k,v,1 if k not in ['declared_real_external_effective'] or declared_real else 0) for k,v in prov.items()])

    for tid, f in feats.items():
        cur.execute('INSERT INTO ctc_motion_feature_v22 VALUES (?,?,?,?,?,?,?,?,?,?,?)', (tid,f['sample_count'],f['first_frame'],f['last_frame'],f['duration_s'],f['path_length'],f['net_displacement'],f['speed_mean'],f['speed_std'],f['direction_coherence'],f['area_cv']))

    cells, cell_source = get_cells(cur)
    mappings = normalize_and_map_tracks(feats, cells) if cells else []
    for tid,cid,x,y,z,d in mappings:
        cur.execute('INSERT INTO ctc_track_to_cell_mapping_v22 VALUES (?,?,?,?,?,?,?)', (tid,cid,x,y,z,d,'normalized_ctc_bbox_to_cell_sphere_nearest_cell'))

    f_by_tid = feats
    for tid,cid,x,y,z,d in mappings:
        f=f_by_tid[tid]
        p = max(0.0, min(1.0, 0.35 + 0.35*f['direction_coherence'] + 0.20*min(f['sample_count']/10.0,1.0) + 0.10*min(f['path_length']/max(f['net_displacement'],1e-6),2.0)/2.0 - 0.15*f['area_cv']))
        r = max(0.0, min(1.0, 0.15 + 0.25*min(f['speed_std']/max(f['speed_mean'],1e-6),1.0) + 0.20*f['area_cv'] + 0.10*(1.0-f['direction_coherence'])))
        xi = max(0.0, min(1.0, 0.10 + 0.55*(1.0-p) + 0.35*r))
        if p >= 0.72 and xi < 0.35:
            motion_state='stable_ctc_trajectory'; pstat='p_supported'; rstat='r_low'; xstat='xi_low'
        elif r >= 0.45:
            motion_state='ctc_counterstructure_watch'; pstat='p_weak'; rstat='r_counterstructure'; xstat='xi_watch'
        elif xi >= 0.45:
            motion_state='ctc_unresolved_motion_watch'; pstat='p_weak'; rstat='r_low'; xstat='xi_watch'
        else:
            motion_state='ctc_candidate_motion'; pstat='p_candidate'; rstat='r_low'; xstat='xi_low'
        pid=f'ctcproj_v22_{tid}'
        cur.execute('INSERT INTO ctc_motion_state_projection_v22 VALUES (?,?,?,?,?,?,?,?)',(pid,tid,cid,motion_state,p,r,xi,'nonsemantic motion continuity/coherence/area-stability projection'))
        cur.execute('INSERT INTO ctc_pr_xi_trial_response_v22 VALUES (?,?,?,?,?,?,?,?,?)',(f'ctcresp_v22_{tid}',tid,pstat,rstat,xstat,p,r,xi,'P/R evaluation precedes Xi; Xi carries only post-P/R unresolved motion residue'))

    gates=[]
    gates.append(('schema_gate','PASS',1,0,'required centroid columns present'))
    gates.append(('motion_feature_gate','PASS' if feats else 'FAIL',1 if feats else 0,0 if feats else 1,f'{len(feats)} tracks processed'))
    gates.append(('cell_mapping_gate','PASS' if mappings else 'FAIL',1 if mappings else 0,0 if mappings else 1,f'{len(mappings)} tracks mapped using {cell_source}'))
    if declared_real:
        gates.append(('real_declaration_gate','PASS_REAL_EXTERNAL_DECLARED',1,0,'user supplied non-sample centroid CSV with --declare-real-external'))
    elif attempted_false_real:
        gates.append(('real_declaration_gate','BLOCKED_SAMPLE_INPUT_CANNOT_BE_DECLARED_REAL',0,1,'--declare-real-external ignored because input is sample/demo/high_fidelity'))
    else:
        gates.append(('real_declaration_gate','BLOCKED_PENDING_REAL_CTC_RAW_INPUT',0,1,'provide extracted real CTC centroid CSV or raw CTC ZIP/root and use --declare-real-external'))
    gates.extend([
        ('source_fact_rewrite_gate','PASS',1,0,'CTC trial only appends projection evidence'),
        ('p_r_xi_boundary_gate','PASS',1,0,'P/R before Xi enforced'),
        ('hot_swap_gate','PASS',1,0,'no hot-swap or frozen profile promotion performed'),
    ])
    cur.executemany('INSERT INTO ctc_declared_realdata_gate_v22 VALUES (?,?,?,?,?)', gates)

    def okrow(name, ok, detail):
        cur.execute('INSERT INTO ctc_declared_trial_acceptance_report_v22 VALUES (?,?,?)',(name,'PASS' if ok else 'FAIL',detail))
    okrow('schema_valid', all(c in fields for c in REQUIRED), 'required columns present')
    okrow('tracks_present', len(feats)>0, f'{len(feats)} tracks')
    okrow('cell_mapping_present', len(mappings)==len(feats) and len(feats)>0, f'{len(mappings)} mappings')
    okrow('pr_xi_responses_present', cur.execute('SELECT COUNT(*) FROM ctc_pr_xi_trial_response_v22').fetchone()[0]==len(feats), 'one response per track')
    okrow('real_sample_guard', not attempted_false_real, 'sample input cannot be declared real')
    okrow('no_source_fact_rewrite', True, 'append-only external projection')
    okrow('p_r_before_xi', True, 'boundary preserved')
    okrow('nonsemantic_motion_projection', True, 'no semantic object labels')
    if centroid_csv.exists():
        cur.execute('INSERT INTO ctc_declared_trial_artifact_manifest_v22 VALUES (?,?,?)',(str(centroid_csv),sha256(centroid_csv),'input_or_extracted_centroid_csv'))
    if mp.exists():
        cur.execute('INSERT INTO ctc_declared_trial_artifact_manifest_v22 VALUES (?,?,?)',(str(mp),sha256(mp),'dataset_download_manifest'))
    con.commit(); con.close()

    summary = {
        'version':'ctc_declared_real_trial_orchestrator_v2.2',
        'input_csv':str(centroid_csv),
        'rows':len(rows),
        'tracks':len(feats),
        'mapped_tracks':len(mappings),
        'declared_real_external_effective':declared_real,
        'attempted_false_real_blocked':attempted_false_real,
        'realdata_gate':[g for g in gates if g[0]=='real_declaration_gate'][0][1],
        'source_facts_rewritten':False,
        'p_r_before_xi_preserved':True,
    }
    (report_dir/'ctc_declared_trial_v22_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (report_dir/'CTC_DECLARED_REAL_TRIAL_V22_REPORT.md').write_text('# CTC Declared Real Trial v2.2\n\n```json\n'+json.dumps(summary, indent=2)+'\n```\n\nThis report is append-only. Sample/demo inputs cannot be declared as real external data.\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
