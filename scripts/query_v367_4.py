#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path

def main():
    db=Path(sys.argv[1]) if len(sys.argv)>1 else Path('m367_4_rmi_default_index_regression.db')
    cmd=sys.argv[2] if len(sys.argv)>2 else 'summary'
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    if cmd=='summary':
        for r in con.execute('select variant_id,production_status,allowed_for_default_query from v3674_rmi_hash_variant order by variant_id'): print(dict(r))
        print('Acceptance:')
        for r in con.execute('select check_name,status,observed_value from v3674_acceptance_report order by check_id'): print(dict(r))
    elif cmd=='bench':
        for r in con.execute('select * from v3674_rmi_query_benchmark order by variant_id'): print(dict(r))
    elif cmd=='gates':
        for r in con.execute('select * from v3674_default_regression_suite order by gate_id'): print(dict(r))
    con.close()
if __name__=='__main__': main()
