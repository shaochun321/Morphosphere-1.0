#!/usr/bin/env python3
import json,sqlite3,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DB=ROOT/'outputs/morphosphere_evidence_reconstruction_v25_output_database.db'
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,default=DB); a=ap.parse_args(); con=sqlite3.connect(a.db); checks=[]
 def ck(n,p,d): checks.append({'check_name':n,'status':'PASS' if p else 'FAIL','passed':int(p),'blocking':1,'detail':d})
 ck('sqlite_quick_check',con.execute('pragma quick_check').fetchone()[0]=='ok','SQLite quick_check ok')
 for t,e in [('information_point_v25',4575),('coordinate_transform_trace_v25',4575),('trajectory_window_trace_v25',532),('calculation_recipe_v25',7),('p_spacetime_measure_v25',532),('r_counter_measure_v25',532),('xi_residual_surface_v25',532),('attention_yield_event_v25',262),('decision_evidence_bundle_v25',532),('evidence_runtime_artifact_manifest_v25',7)]:
  x=con.execute(f'select count(*) from {t}').fetchone()[0]; ck('count_'+t,x==e,f'expected {e}, actual {x}')
 ck('xi_reentry_policy',con.execute("select count(*) from xi_residual_surface_v25 where reentry_policy!='via_o_candidate_only'").fetchone()[0]==0,'Xi via O candidate only')
 ck('external_entropy_refs',con.execute("select count(*) from decision_evidence_bundle_v25 where external_ledger_refs_json like '%win_%'").fetchone()[0]==532,'532/532 bundles link external entropy ledger')
 print(json.dumps({'status':'PASS' if all(c['passed'] for c in checks) else 'FAIL','checks':checks},indent=2,ensure_ascii=False))
 return 0 if all(c['passed'] for c in checks) else 1
if __name__=='__main__': raise SystemExit(main())
