#!/usr/bin/env python3
import argparse, sqlite3, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Inspect v32 generalized source adapter and scale contract state.')
    ap.add_argument('--db', default='outputs/m32.db')
    args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor()
    print('V32 GENERALIZED SOURCE ADAPTER STATUS')
    for t in ['v32_source_adapter_registry','v32_scale_contract','v32_general_source_event','v32_adapter_output_mapping','v32_cross_source_normalization_probe','v32_acceptance_report']:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        print(f'{t}: {cur.fetchone()[0]}')
    print('quick_check:', cur.execute('PRAGMA quick_check').fetchone()[0])
if __name__=='__main__': main()
