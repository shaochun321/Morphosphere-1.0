#!/usr/bin/env python3
import argparse, sqlite3

def main():
 p=argparse.ArgumentParser(); p.add_argument('db'); a=p.parse_args(); con=sqlite3.connect(a.db); cur=con.cursor(); checks=[]
 def s(sql,default=0):
  try:
   r=cur.execute(sql).fetchone(); return r[0] if r else default
  except Exception: return default
 def exists(t): return s(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{t}'",0)==1
 def add(n,ok,obs='',exp=''): checks.append((n,ok,obs,exp))
 tabs=['realdata_review_run_manifest_v09','external_data_ingestion_contract_v09','external_data_file_register_v09','external_physical_sample_v09','external_sample_cell_mapping_v09','external_data_quality_gate_v09','realdata_calibration_result_v09','candidate_patch_manual_review_packet_v09','candidate_patch_application_decision_v09','source_fact_digest_v09','realdata_review_acceptance_report_v09','realdata_review_artifact_manifest_v09']
 for t in tabs:
  add('exists_'+t,exists(t),exists(t),True); add('nonempty_'+t,s(f'SELECT COUNT(*) FROM {t}',0)>0,s(f'SELECT COUNT(*) FROM {t}',0),'>0')
 add('source_facts_unchanged',s("SELECT COUNT(*) FROM source_fact_digest_v09 WHERE status!='PASS'",0)==0,s("SELECT COUNT(*) FROM source_fact_digest_v09 WHERE status!='PASS'",0),0)
 add('candidate_not_auto_applied',s('SELECT SUM(auto_applied) FROM candidate_patch_application_decision_v09',0)==0,s('SELECT SUM(auto_applied) FROM candidate_patch_application_decision_v09',0),0)
 add('manual_review_required',s('SELECT MIN(manual_review_required) FROM candidate_patch_application_decision_v09',0)==1,s('SELECT MIN(manual_review_required) FROM candidate_patch_application_decision_v09',0),1)
 add('schema_valid',s('SELECT MIN(schema_valid) FROM realdata_calibration_result_v09',0)==1,s('SELECT MIN(schema_valid) FROM realdata_calibration_result_v09',0),1)
 add('mapping_complete',s('SELECT sample_count=mapped_sample_count FROM realdata_calibration_result_v09 LIMIT 1',0)==1,s('SELECT sample_count||"/"||mapped_sample_count FROM realdata_calibration_result_v09 LIMIT 1',''), 'equal')
 add('real_data_gate_recorded',s("SELECT real_data_gate_status FROM realdata_calibration_result_v09 LIMIT 1",'') in ('BLOCKED_PENDING_REAL_EXTERNAL_DATA','REAL_DATA_TRIAL_REVIEW_REQUIRED'),s("SELECT real_data_gate_status FROM realdata_calibration_result_v09 LIMIT 1",''),'known')
 add('p_r_xi_boundary_gate_pass',s("SELECT COUNT(*) FROM external_data_quality_gate_v09 WHERE gate_name='p_r_xi_boundary_preserved' AND gate_status='PASS'",0)==1,s("SELECT COUNT(*) FROM external_data_quality_gate_v09 WHERE gate_name='p_r_xi_boundary_preserved' AND gate_status='PASS'",0),1)
 add('review_packet_artifact_present',s("SELECT COUNT(*) FROM realdata_review_artifact_manifest_v09 WHERE artifact_role='manual_review_packet'",0)==1,s("SELECT COUNT(*) FROM realdata_review_artifact_manifest_v09 WHERE artifact_role='manual_review_packet'",0),1)
 passed=sum(1 for _,ok,_,_ in checks if ok)
 for n,ok,obs,exp in checks: print(f"{'PASS' if ok else 'FAIL'} {n}: observed={obs} expected={exp}")
 print(f'SUMMARY: {passed}/{len(checks)} PASS')
 if passed!=len(checks): raise SystemExit(1)
if __name__=='__main__': main()
