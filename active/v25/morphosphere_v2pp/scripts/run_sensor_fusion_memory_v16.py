#!/usr/bin/env python3
import argparse, sqlite3, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Report v1.6 sensor fusion memory status from an existing DB.')
    ap.add_argument('--db', required=True)
    ap.add_argument('--runtime-dir', default='runtime_store/v16')
    ap.add_argument('--report-dir', default='morphosphere_v2pp/reports')
    args=ap.parse_args()
    con=sqlite3.connect(args.db)
    cur=con.cursor()
    checks=cur.execute('select count(*), sum(passed) from sensor_fusion_memory_acceptance_report_v16').fetchone()
    print(f'sensor_fusion_memory_v1.6 acceptance stored: {checks[1]} / {checks[0]} PASS')
    for t in ['clock_domain_memory_state_v16','phase_bias_memory_state_v16','fusion_confidence_memory_trace_v16','domain_calibration_recommendation_v16','drift_memory_replay_result_v16']:
        print(t, cur.execute(f'select count(*) from {t}').fetchone()[0])
    con.close()
if __name__=='__main__': main()
