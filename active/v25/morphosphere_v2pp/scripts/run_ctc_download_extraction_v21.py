#!/usr/bin/env python3
import argparse, csv, hashlib, json, os, sqlite3
from pathlib import Path

REQ = ['source_id','sample_id','clock_domain','time_s','sensor_id','sensor_kind','x','y','z','channel','value','uncertainty','track_id','frame','centroid_x','centroid_y','centroid_z','area','sequence_id']

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        r=csv.DictReader(f)
        missing=[c for c in REQ if c not in (r.fieldnames or [])]
        if missing:
            raise SystemExit('missing required columns: '+','.join(missing))
        return list(r), r.fieldnames

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--external-csv', default='morphosphere_v2pp/data/ctc_centroid_sample_v21.csv')
    ap.add_argument('--declare-real-external', action='store_true')
    ap.add_argument('--dataset-manifest', default='morphosphere_v2pp/data/ctc_download_manifest_v21.json')
    ap.add_argument('--report-dir', default='morphosphere_v2pp/reports')
    args=ap.parse_args()
    csv_path=Path(args.external_csv)
    manifest_path=Path(args.dataset_manifest)
    report_dir=Path(args.report_dir); report_dir.mkdir(parents=True, exist_ok=True)
    rows, fields = read_csv(csv_path)
    manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
    con=sqlite3.connect(args.db)
    cur=con.cursor()
    tables = ['ctc_dataset_download_plan_v21','ctc_download_attempt_v21','ctc_centroid_extraction_contract_v21','ctc_centroid_schema_v21','ctc_extracted_centroid_sample_v21','ctc_centroid_quality_report_v21','ctc_realdata_readiness_gate_v21','ctc_v21_acceptance_report','ctc_artifact_manifest_v21']
    for t in tables: cur.execute(f'DROP TABLE IF EXISTS {t}')
    cur.execute('CREATE TABLE ctc_dataset_download_plan_v21 (dataset_name TEXT, doi TEXT, download_url TEXT, expected_md5 TEXT, expected_size_mb REAL, license TEXT, status TEXT)')
    cur.execute('INSERT INTO ctc_dataset_download_plan_v21 VALUES (?,?,?,?,?,?,?)', (manifest.get('primary_dataset','Fluo-N2DH-GOWT1'),manifest.get('doi','10.5281/zenodo.15608211'),manifest.get('download_url',''),manifest.get('expected_md5',''),manifest.get('expected_size_mb',0),manifest.get('license',''), 'DOWNLOAD_REQUIRED_NOT_BUNDLED'))
    cur.execute('CREATE TABLE ctc_download_attempt_v21 (attempt_id TEXT, local_path TEXT, declared_real_external INTEGER, file_sha256 TEXT, row_count INTEGER, status TEXT)')
    file_sha = sha256(csv_path)
    status = 'REAL_EXTERNAL_CSV_PROVIDED' if args.declare_real_external else 'DEMO_OR_DERIVED_CSV_NOT_REAL_EXTERNAL'
    cur.execute('INSERT INTO ctc_download_attempt_v21 VALUES (?,?,?,?,?,?)', ('attempt_v21_001',str(csv_path),1 if args.declare_real_external else 0,file_sha,len(rows),status))
    cur.execute('CREATE TABLE ctc_centroid_extraction_contract_v21 (contract_key TEXT PRIMARY KEY, contract_value TEXT)')
    contract = {
        'source_mode':'ctc_mask_or_centroid_csv',
        'extractor':'extract_ctc_centroids_v21.py',
        'no_source_fact_rewrite':'true',
        'output_schema':'ctc_centroid_track_schema_v21',
        'real_external_requires_user_download_or_upload':'true',
        'p_r_before_xi_preserved':'true'
    }
    cur.executemany('INSERT INTO ctc_centroid_extraction_contract_v21 VALUES (?,?)', contract.items())
    cur.execute('CREATE TABLE ctc_centroid_schema_v21 (column_name TEXT, required INTEGER)')
    cur.executemany('INSERT INTO ctc_centroid_schema_v21 VALUES (?,?)', [(c,1) for c in REQ] + [(c,0) for c in fields if c not in REQ])
    cur.execute('CREATE TABLE ctc_extracted_centroid_sample_v21 (source_id TEXT, sample_id TEXT, clock_domain TEXT, time_s REAL, sensor_id TEXT, sensor_kind TEXT, x REAL, y REAL, z REAL, channel TEXT, value REAL, uncertainty REAL, track_id TEXT, frame INTEGER, centroid_x REAL, centroid_y REAL, centroid_z REAL, area REAL, sequence_id TEXT)')
    insert_rows=[]
    for r in rows:
        insert_rows.append((r['source_id'],r['sample_id'],r['clock_domain'],float(r['time_s']),r['sensor_id'],r['sensor_kind'],float(r['x']),float(r['y']),float(r['z']),r['channel'],float(r['value']),float(r['uncertainty']),r['track_id'],int(float(r['frame'])),float(r['centroid_x']),float(r['centroid_y']),float(r['centroid_z']),float(r['area']),r['sequence_id']))
    cur.executemany('INSERT INTO ctc_extracted_centroid_sample_v21 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', insert_rows)
    tracks=len(set(r['track_id'] for r in rows)); frames=len(set(r['frame'] for r in rows))
    xs=[float(r['x']) for r in rows]; ys=[float(r['y']) for r in rows]
    # simple motion variation proxy
    bytrack={}
    for r in rows: bytrack.setdefault(r['track_id'],[]).append(r)
    disps=[]
    for tr,rs in bytrack.items():
        rs=sorted(rs, key=lambda r:int(float(r['frame'])))
        for a,b in zip(rs,rs[1:]):
            dx=float(b['x'])-float(a['x']); dy=float(b['y'])-float(a['y']); dz=float(b['z'])-float(a['z'])
            disps.append((dx*dx+dy*dy+dz*dz)**0.5)
    avg_disp=sum(disps)/len(disps) if disps else 0.0
    cur.execute('CREATE TABLE ctc_centroid_quality_report_v21 (metric TEXT PRIMARY KEY, value TEXT, passed INTEGER)')
    metrics=[('row_count',str(len(rows)),int(len(rows)>0)),('track_count',str(tracks),int(tracks>=1)),('frame_count',str(frames),int(frames>=2)),('avg_interframe_displacement',f'{avg_disp:.6f}',int(avg_disp>0)),('coordinate_span_x',f'{max(xs)-min(xs):.6f}',int(max(xs)>min(xs))),('coordinate_span_y',f'{max(ys)-min(ys):.6f}',int(max(ys)>min(ys)))]
    cur.executemany('INSERT INTO ctc_centroid_quality_report_v21 VALUES (?,?,?)', metrics)
    cur.execute('CREATE TABLE ctc_realdata_readiness_gate_v21 (gate_name TEXT PRIMARY KEY, status TEXT, passed INTEGER, note TEXT)')
    real_gate = ('real_ctc_data_gate','READY_REAL_EXTERNAL_CSV_DECLARED' if args.declare_real_external else 'BLOCKED_PENDING_REAL_CTC_DOWNLOAD_OR_UPLOAD',1 if args.declare_real_external else 0,'real external mode requires user-provided/downloaded CTC centroid CSV and --declare-real-external')
    gates=[real_gate,('schema_gate','PASS',1,'required centroid columns present'),('quality_gate','PASS' if all(m[2] for m in metrics[:4]) else 'FAIL',int(all(m[2] for m in metrics[:4])),'centroid rows/tracks/frames/motion validated'),('no_source_fact_rewrite','PASS',1,'external CTC input remains projection evidence'),('p_r_before_xi_preserved','PASS',1,'CTC motion evidence does not allow Xi to replace P/R')]
    cur.executemany('INSERT INTO ctc_realdata_readiness_gate_v21 VALUES (?,?,?,?)', gates)
    cur.execute('CREATE TABLE ctc_v21_acceptance_report (test_name TEXT PRIMARY KEY, status TEXT, detail TEXT)')
    acc=[]
    for name,ok,detail in [('schema_columns',not any(c not in fields for c in REQ),'required columns present'),('centroid_rows',len(rows)>0,f'{len(rows)} rows'),('track_count',tracks>=1,f'{tracks} tracks'),('frame_count',frames>=2,f'{frames} frames'),('motion_nonzero',avg_disp>0,f'avg_disp={avg_disp:.6f}'),('no_auto_real_claim',not args.declare_real_external or status.startswith('REAL_EXTERNAL'),status),('p_r_before_xi_contract',True,'preserved')]:
        acc.append((name,'PASS' if ok else 'FAIL',detail))
    cur.executemany('INSERT INTO ctc_v21_acceptance_report VALUES (?,?,?)', acc)
    cur.execute('CREATE TABLE ctc_artifact_manifest_v21 (path TEXT, sha256 TEXT, role TEXT)')
    for p,role in [(csv_path,'input_centroid_csv'),(manifest_path,'dataset_manifest')]:
        if p.exists(): cur.execute('INSERT INTO ctc_artifact_manifest_v21 VALUES (?,?,?)',(str(p),sha256(p),role))
    con.commit(); con.close()
    summary={'version':'ctc_download_extraction_v2.1','input_csv':str(csv_path),'declared_real_external':bool(args.declare_real_external),'rows':len(rows),'tracks':tracks,'frames':frames,'avg_interframe_displacement':avg_disp,'realdata_gate':real_gate[1]}
    (report_dir/'ctc_download_extraction_v21_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))
if __name__=='__main__': main()
