#!/usr/bin/env python3
import argparse, sqlite3

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', default='outputs/m36.db')
    ap.add_argument('--limit', type=int, default=5)
    args=ap.parse_args()
    con=sqlite3.connect(args.db); c=con.cursor()
    print('Top dissipative steady-source candidates:')
    sql1 = "SELECT source_id, source_kind, D_var, F_ext_var, SNR_struct, steady_source_status FROM v36_dissipative_source_registry ORDER BY steady_source_candidate DESC, SNR_struct DESC LIMIT ?"
    for row in c.execute(sql1,(args.limit,)):
        print(row)
    print('\nHighest curvature proxy rows:')
    sql2 = "SELECT curvature_id, region_ref, K_proxy, ricci_claimed FROM v36_curvature_proxy ORDER BY K_proxy DESC LIMIT ?"
    for row in c.execute(sql2,(args.limit,)):
        print(row)
    print('\nMetric anchor warnings:')
    sql3 = "SELECT anchor_audit_id, metric_id, drift_ratio, status, recommendation FROM v36_metric_anchor_audit WHERE status!='PASS' ORDER BY drift_ratio DESC LIMIT ?"
    for row in c.execute(sql3,(args.limit,)):
        print(row)
    con.close()
if __name__=='__main__': main()
