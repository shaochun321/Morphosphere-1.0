#!/usr/bin/env python3
import argparse, sqlite3, sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--db', default='outputs/m36.db'); args=ap.parse_args()
    con=sqlite3.connect(args.db); c=con.cursor()
    failures=[]
    # No mainline physical truth claims in downgrade contract.
    forbidden=['physical spacetime metric','true differential field','Ricci curvature','physical singularity','true topology surgery']
    for text in forbidden:
        n=c.execute("SELECT COUNT(*) FROM v36_downgrade_contract WHERE forbidden_interpretation LIKE ?",('%'+text+'%',)).fetchone()[0]
        print('forbidden interpretation present:', text, n)
        if n == 0: failures.append(text)
    # Delta Xin must be fallback only.
    n=c.execute('SELECT COUNT(*) FROM v36_delta_xin_field WHERE fallback_only != 1').fetchone()[0]
    print('delta_xin_not_fallback_only:', n)
    if n: failures.append('delta_xin_fallback')
    # Coordinates must not be replaced.
    n=c.execute('SELECT COUNT(*) FROM v36_information_energy_metric_proxy WHERE raw_coordinate_replaced != 0').fetchone()[0]
    print('raw_coordinate_replaced_rows:', n)
    if n: failures.append('coordinate_replacement')
    # Curvature must not claim Ricci.
    n=c.execute('SELECT COUNT(*) FROM v36_curvature_proxy WHERE ricci_claimed != 0').fetchone()[0]
    print('ricci_claimed_rows:', n)
    if n: failures.append('ricci_claim')
    con.close()
    if failures:
        print('FAIL downgrade audit:', failures); sys.exit(1)
    print('PASS downgrade audit')
if __name__=='__main__': main()
