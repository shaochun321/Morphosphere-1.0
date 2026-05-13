#!/usr/bin/env python3
import argparse, sqlite3, sys
EXPECTED = {
    'v36_run_manifest': 1,
    'v36_dissipative_source_registry': 80,
    'v36_information_energy_metric_proxy': 160,
    'v36_metric_anchor_audit': 160,
    'v36_curvature_proxy': 120,
    'v36_downgrade_contract': 7,
    'v36_acceptance_report': 12,
}
REQUIRED_PASS = ['source_facts_rewritten','hot_swap_allowed','semantic_label_in_mainline','physical_metric_claimed','delta_xin_as_main_definition','ricci_claimed','coordinate_replaced']

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='outputs/m36.db')
    args=ap.parse_args()
    con=sqlite3.connect(args.db); c=con.cursor()
    ok=True
    qc=c.execute('pragma quick_check(1)').fetchone()[0]
    print('SQLite quick_check:', qc)
    ok &= (qc == 'ok')
    for table, min_count in EXPECTED.items():
        n=c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {n}')
        ok &= n >= min_count
    bad=c.execute("SELECT COUNT(*) FROM v36_acceptance_report WHERE status!='PASS'").fetchone()[0]
    print('acceptance non-pass:', bad)
    ok &= bad == 0
    for guard in REQUIRED_PASS:
        row=c.execute('SELECT status FROM v36_metric_guardrail_audit WHERE guard_name=?',(guard,)).fetchone()
        print('guard', guard, row[0] if row else 'MISSING')
        ok &= row is not None and row[0]=='PASS'
    manifest=c.execute('SELECT includes_full_base, not_a_full_lineage, source_facts_rewritten, semantic_label_in_mainline, physical_metric_claimed FROM v36_run_manifest').fetchone()
    print('manifest flags:', manifest)
    ok &= manifest == (0,1,0,0,0)
    con.close()
    if not ok:
        print('FAIL v36 metric bridge overlay')
        sys.exit(1)
    print('PASS v36 metric bridge overlay')
if __name__=='__main__': main()
