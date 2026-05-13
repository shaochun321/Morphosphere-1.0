#!/usr/bin/env python3
import argparse, sqlite3
p=argparse.ArgumentParser(); p.add_argument('--db',default='outputs/m361.db'); a=p.parse_args()
con=sqlite3.connect(a.db); cur=con.cursor()
print('Suspended functionals:')
for row in cur.execute("SELECT functional_id,functional_name,engineering_downgrade,forbidden_interpretation FROM v361_action_functional_registry WHERE status='suspended'"):
 print(row)
print('Downgrade contracts:')
for row in cur.execute('SELECT item_id,downgraded_engineering_object,minimization_or_revision FROM v361_downgrade_contract ORDER BY item_id'):
 print(row)
