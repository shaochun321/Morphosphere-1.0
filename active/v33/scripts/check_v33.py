#!/usr/bin/env python3
import argparse, sqlite3, sys
p=argparse.ArgumentParser(); p.add_argument('--db', default='outputs/m33.db'); args=p.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor()
checks={}
checks['quick_check']=cur.execute('pragma quick_check').fetchone()[0]=='ok'
for name in ['v33_bottom_adapter_registry','v33_legacy_module_crosswalk','v33_bottom_prediction_event','v33_bottom_predicted_edge','v33_prediction_to_source_event_mapping','v33_acceptance_report']:
    cnt=cur.execute(f'select count(*) from {name}').fetchone()[0]
    checks[name]=cnt>0
    print(f'{name}: {cnt}')
manifest=cur.execute('select source_facts_rewritten,hot_swap_allowed,legacy_direct_active_allowed,prediction_only from v33_run_manifest').fetchone()
checks['guardrails']=manifest==(0,0,0,1)
acc=cur.execute("select count(*) from v33_acceptance_report where status='PASS'").fetchone()[0]
total=cur.execute('select count(*) from v33_acceptance_report').fetchone()[0]
print(f'v33_acceptance_report: {acc}/{total} PASS')
print('guardrails:', manifest)
ok=all(checks.values()) and acc==total
print('V33_BOTTOM_PREDICTION_ADAPTER_ACCEPTANCE:', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
