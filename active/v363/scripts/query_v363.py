#!/usr/bin/env python3
import argparse, sqlite3, json
parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
parser.add_argument('--limit', type=int, default=5)
parser.add_argument('--mode', choices=['bands','xin','pseudo'], default='bands')
args = parser.parse_args()
con = sqlite3.connect(args.db)
con.row_factory = sqlite3.Row
cur = con.cursor()
if args.mode == 'bands':
    rows = cur.execute('SELECT * FROM v363_r_spacetime_band_candidate ORDER BY continuity_cost LIMIT ?', (args.limit,)).fetchall()
elif args.mode == 'xin':
    rows = cur.execute('SELECT * FROM v363_xin_noncontinuity_ledger ORDER BY continuity_dilution_index DESC LIMIT ?', (args.limit,)).fetchall()
else:
    rows = cur.execute('SELECT * FROM v363_pseudo_continuity_audit ORDER BY structural_continuity_index DESC LIMIT ?', (args.limit,)).fetchall()
for row in rows:
    print(json.dumps(dict(row), ensure_ascii=False))
