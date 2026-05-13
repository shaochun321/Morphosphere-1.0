#!/usr/bin/env python3
import argparse, sqlite3, sys, json

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('db'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor()
    tests=[]
    def count(t):
        return cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    def add(name, ok, detail): tests.append((name, ok, detail))
    try:
        qc=cur.execute('PRAGMA quick_check').fetchone()[0]
        add('quick_check', qc=='ok', qc)
    except Exception as e: add('quick_check', False, str(e))
    for t in ['ctc_declared_trial_run_manifest_v22','ctc_motion_feature_v22','ctc_track_to_cell_mapping_v22','ctc_pr_xi_trial_response_v22','ctc_declared_realdata_gate_v22']:
        try: add(t, count(t)>0, str(count(t)))
        except Exception as e: add(t, False, str(e))
    try:
        gates=dict((r[0],r[1]) for r in cur.execute('SELECT gate_name,gate_status FROM ctc_declared_realdata_gate_v22'))
        add('real_declaration_gate_present','real_declaration_gate' in gates, gates.get('real_declaration_gate','missing'))
        add('p_r_xi_boundary_gate', gates.get('p_r_xi_boundary_gate')=='PASS', gates.get('p_r_xi_boundary_gate','missing'))
        add('source_fact_rewrite_gate', gates.get('source_fact_rewrite_gate')=='PASS', gates.get('source_fact_rewrite_gate','missing'))
    except Exception as e: add('gate_checks', False, str(e))
    try:
        statuses=[r[0] for r in cur.execute('SELECT DISTINCT p_status FROM ctc_pr_xi_trial_response_v22')]
        add('pr_response_diversity', len(statuses)>=1, json.dumps(statuses))
    except Exception as e: add('pr_response_diversity', False, str(e))
    passed=sum(1 for _,ok,_ in tests if ok)
    for name,ok,detail in tests: print(('PASS' if ok else 'FAIL'), name, detail)
    print(f'ctc_declared_trial_v2.2 acceptance: {passed} / {len(tests)} PASS')
    sys.exit(0 if passed==len(tests) else 1)
if __name__=='__main__': main()
