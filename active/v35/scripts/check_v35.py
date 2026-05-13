#!/usr/bin/env python3
import argparse, sqlite3
REQ={
 'v35_run_manifest':1,'v35_attention_region_index':160,'v35_attention_tension_map':160,
 'v35_p_inertia_profile':59,'v35_r_counter_chain':120,'v35_xi_momentum_chain':32,
 'v35_masking_proposal':16,'v35_attention_proposal':120,'v35_attention_transition_log':119,
 'v35_attentional_path_integral_audit':120,'v35_boundary_leakage_audit':40,
 'v35_attention_performance_report':120,'v35_guardrail_audit':8,'v35_acceptance_report':12}
ap=argparse.ArgumentParser(); ap.add_argument('--db',default='outputs/m35.db'); args=ap.parse_args()
con=sqlite3.connect(args.db); cur=con.cursor(); assert cur.execute('pragma quick_check(1)').fetchone()[0]=='ok'
fail=[]
for t,n in REQ.items():
    c=cur.execute(f'select count(*) from {t}').fetchone()[0]
    if c!=n: fail.append((t,c,n))
if cur.execute('select count(*) from v35_attention_proposal where sandbox_only!=1 or real_action_authorized!=0').fetchone()[0]: fail.append(('proposal_guardrail',1,0))
if cur.execute('select count(*) from v35_xi_momentum_chain where direct_to_p_allowed!=0').fetchone()[0]: fail.append(('xi_direct_to_p',1,0))
if fail:
    print('FAIL', fail); raise SystemExit(1)
print('MORPHOSPHERE_V35_ENGINEERED_BRIDGE_OVERLAY_ACCEPTANCE: PASS')
for t in REQ: print(f'{t}: {cur.execute(f"select count(*) from {t}").fetchone()[0]}')
