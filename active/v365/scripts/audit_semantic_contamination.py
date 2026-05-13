#!/usr/bin/env python3
"""Re-run a lightweight semantic field audit over v365 mainline tables."""
import argparse, sqlite3, json
FORBIDDEN = ['semantic_label','meaning','truth_label','object_name','behavior_type','biological_state','final_interpretation']
MAINLINE = ['v365_upper_recursion_semantic_null_contract','v365_xin_minimal_carrier_state','v365_external_real_input_envelope_binding','v365_xin_reentry_policy']
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m365.db'); args=p.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor()
report=[]
for t in MAINLINE:
    cols=[r[1] for r in cur.execute(f'pragma table_info({t})')]
    hits=[c for c in cols if any(term in c.lower() for term in FORBIDDEN)]
    report.append({'table':t,'forbidden_column_hits':hits,'status':'FAIL' if hits else 'PASS'})
print(json.dumps(report, ensure_ascii=False, indent=2))
if any(x['status']=='FAIL' for x in report):
    raise SystemExit(1)
