#!/usr/bin/env python3
import argparse,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; DB=ROOT/'outputs/morphosphere_evidence_reconstruction_v25_output_database.db'
def load(x):
 try: return json.loads(x) if isinstance(x,str) and (x.startswith('[') or x.startswith('{')) else x
 except Exception: return x
def rd(r): return None if r is None else {k:load(r[k]) for k in r.keys()}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--db',type=Path,default=DB); ap.add_argument('--id',required=True); ap.add_argument('--limit-points',type=int,default=6); a=ap.parse_args(); con=sqlite3.connect(a.db); con.row_factory=sqlite3.Row; q=a.id
 if q.startswith('eb25_'): b=con.execute('select * from decision_evidence_bundle_v25 where bundle_id=?',(q,)).fetchone()
 elif q.startswith('p25_'): b=con.execute('select * from decision_evidence_bundle_v25 where p_measure_id=?',(q,)).fetchone()
 elif q.startswith('r25_'): b=con.execute('select * from decision_evidence_bundle_v25 where r_measure_id=?',(q,)).fetchone()
 elif q.startswith('xi25_'): b=con.execute('select * from decision_evidence_bundle_v25 where xi_surface_id=?',(q,)).fetchone()
 else: b=con.execute('select * from decision_evidence_bundle_v25 where trajectory_trace_refs_json like ?',(f'%{q}%',)).fetchone()
 if not b: raise SystemExit('not found: '+q)
 b=rd(b); tw=rd(con.execute('select * from trajectory_window_trace_v25 where trajectory_trace_id=?',(b['trajectory_trace_refs_json'][0],)).fetchone()); p=rd(con.execute('select * from p_spacetime_measure_v25 where p_measure_id=?',(b['p_measure_id'],)).fetchone()); r=rd(con.execute('select * from r_counter_measure_v25 where r_measure_id=?',(b['r_measure_id'],)).fetchone()); xi=rd(con.execute('select * from xi_residual_surface_v25 where xi_surface_id=?',(b['xi_surface_id'],)).fetchone()); pts=[]; trs=[]
 for pid in b['source_point_refs_json'][:a.limit_points]:
  pts.append(rd(con.execute('select * from information_point_v25 where point_id=?',(pid,)).fetchone())); trs.append(rd(con.execute('select * from coordinate_transform_trace_v25 where source_point_id=?',(pid,)).fetchone()))
 print(json.dumps({'bundle':b,'trajectory_window':tw,'p_measure':p,'r_measure':r,'xi_surface':xi,'sample_points':pts,'sample_coordinate_transforms':trs,'note':'source reversible and process replayable; support-domain reprojectable, not raw image inversion'},indent=2,ensure_ascii=False))
if __name__=='__main__': main()
