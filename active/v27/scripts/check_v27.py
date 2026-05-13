#!/usr/bin/env python3
import argparse, sqlite3, sys
ap=argparse.ArgumentParser()
ap.add_argument('--db', default='outputs/m27.db')
args=ap.parse_args()
con=sqlite3.connect(args.db)
cur=con.cursor()
print('SQLite quick_check:', cur.execute('PRAGMA quick_check(1)').fetchone()[0])
for t in ['v27_measure_point_sample','v27_measure_field_cell','v27_reversible_query_index','v27_measure_recipe_trace','v27_reconstruction_query_sample','v27_field_grid_spec','v27_acceptance_report']:
    print(f'{t}:', cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0])
rows=cur.execute('SELECT check_id,status,detail FROM v27_acceptance_report ORDER BY check_id').fetchall()
for row in rows: print(*row, sep=' | ')
if any(r[1] != 'PASS' for r in rows):
    sys.exit(1)
print('V27_ACCEPTANCE: PASS')
