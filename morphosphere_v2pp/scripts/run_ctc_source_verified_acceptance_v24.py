#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path

def main():
    db=Path(sys.argv[1]) if len(sys.argv)>1 else Path('outputs/morphosphere_ctc_source_verified_v24_output_database.db')
    con=sqlite3.connect(db); cur=con.cursor(); tests=[]
    def add(name, ok, detail=''):
        tests.append((name, ok, detail)); print(('PASS' if ok else 'FAIL'), name, detail)
    try: add('quick_check', cur.execute('PRAGMA quick_check').fetchone()[0]=='ok')
    except Exception as e: add('quick_check', False, str(e))
    def count(t): return cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    for t in ['ctc_source_zip_provenance_v24','ctc_source_centroid_extraction_v24','ctc_source_verified_gate_v24','ctc_source_verified_acceptance_report_v24','ctc_source_verified_artifact_manifest_v24']:
        try: add(t, count(t)>0, str(count(t)))
        except Exception as e: add(t, False, str(e))
    try: add('real_declaration_gate', cur.execute("SELECT passed FROM ctc_source_verified_gate_v24 WHERE gate_name='real_external_declared'").fetchone()[0]==1)
    except Exception as e: add('real_declaration_gate', False, str(e))
    try: add('centroid_rows_4575', cur.execute("SELECT value FROM ctc_source_centroid_extraction_v24 WHERE metric='row_count'").fetchone()[0]=='4575')
    except Exception as e: add('centroid_rows_4575', False, str(e))
    try: add('tracks_86', cur.execute("SELECT value FROM ctc_source_centroid_extraction_v24 WHERE metric='track_count'").fetchone()[0]=='86')
    except Exception as e: add('tracks_86', False, str(e))
    try: add('p_r_before_xi', cur.execute("SELECT passed FROM ctc_source_verified_gate_v24 WHERE gate_name='p_r_before_xi'").fetchone()[0]==1)
    except Exception as e: add('p_r_before_xi', False, str(e))
    ok=sum(1 for _,b,_ in tests if b); print(f'ctc_source_verified_v2.4 acceptance: {ok} / {len(tests)} PASS')
    if ok!=len(tests): sys.exit(1)
if __name__=='__main__': main()
