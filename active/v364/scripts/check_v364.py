#!/usr/bin/env python3
import argparse, sqlite3, sys
REQUIRED = {
 'v364_artifact_identity': 10,
 'v364_p_anchor_tunnel_profile': 60,
 'v364_dissipation_light_cone': 240,
 'v364_r_band_candidate_search': 120,
 'v364_dynamic_beam_state': 500,
 'v364_variational_coupling_cost': 120,
 'v364_xin_triage_policy': 80,
 'v364_pseudo_continuity_score': 120,
 'v364_cognitive_field_residual_audit': 40,
 'v364_coupler_decision_report': 40,
 'v364_downgrade_contract': 9,
 'v364_acceptance_report': 12,
}
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='outputs/m364.db')
    args=ap.parse_args()
    con=sqlite3.connect(args.db)
    qc=con.execute('PRAGMA quick_check').fetchone()[0]
    if qc!='ok':
        print('FAIL quick_check', qc); return 1
    ok=True
    for table, minimum in REQUIRED.items():
        n=con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {n}')
        if n < minimum:
            ok=False
    ident=dict(con.execute('SELECT key,value FROM v364_artifact_identity'))
    guards = {
        'artifact_type':'ENGINEERED_BRIDGE_OVERLAY',
        'includes_full_base':'false',
        'not_a_full_lineage':'true',
        'semantic_label_in_mainline':'0',
        'global_optimum_claimed':'0',
        'physical_field_equation_claimed':'0',
    }
    for k,v in guards.items():
        got=ident.get(k)
        print(f'guard {k}={got}')
        if got != v:
            ok=False
    failures=con.execute("SELECT COUNT(*) FROM v364_acceptance_report WHERE status!='PASS'").fetchone()[0]
    if failures:
        print('FAIL acceptance failures', failures); ok=False
    sem=con.execute('SELECT COUNT(*) FROM v364_p_anchor_tunnel_profile WHERE semantic_label IS NOT NULL').fetchone()[0]
    if sem:
        print('FAIL semantic labels in mainline', sem); ok=False
    loss=con.execute('SELECT COUNT(*) FROM v364_cognitive_field_residual_audit WHERE used_as_loss!=0').fetchone()[0]
    if loss:
        print('FAIL field residual used as loss', loss); ok=False
    con.close()
    print('PASS v36.4' if ok else 'FAIL v36.4')
    return 0 if ok else 2
if __name__ == '__main__':
    sys.exit(main())
