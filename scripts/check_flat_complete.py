#!/usr/bin/env python3
import os, sys, sqlite3, json
from pathlib import Path

def q1(db, sql, default=None):
    try:
        con=sqlite3.connect(db); cur=con.cursor(); cur.execute(sql); row=cur.fetchone(); con.close(); return row[0] if row else default
    except Exception:
        return default

def integrity(db):
    try:
        con=sqlite3.connect(db); cur=con.cursor(); cur.execute('PRAGMA integrity_check'); row=cur.fetchone(); con.close(); return row[0]
    except Exception as e:
        return 'ERROR: '+str(e)

def table_count(db, table):
    return q1(db, f"SELECT COUNT(*) FROM {table}", None)

def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
    summary_only='--summary-only' in sys.argv
    checks=[
        ('base m25', root/'outputs/m25.db'),
        ('base m34', root/'outputs/m34.db'),
        ('v365 full rebase', root/'outputs/m365_full_rebase.db'),
        ('v366 materialized', root/'outputs/v366/m365_full_chain_materialized.db'),
        ('v366 process window', root/'outputs/v366/m366_process_window_pass3.db'),
        ('v367 native anchor', root/'outputs/v367/m367_1_native_anchor_hardening.db'),
        ('v367 rmi index', root/'outputs/v367/m367_4_rmi_default_index_regression.db'),
        ('v368 final mainline', root/'outputs/v368/m368_mainline_consolidated_final.db'),
        ('v370 runtime prototype', root/'outputs/v370/m370_native_runtime_prototype.db'),
    ]
    failed=[]
    print('Morphosphere v37.0 flat complete package summary')
    print('root:', root)
    for name, db in checks:
        if not db.exists():
            print(f'MISSING {name}: {db}')
            failed.append(name)
            continue
        ic=integrity(db)
        print(f'{name}: integrity={ic} size={db.stat().st_size}')
        if ic!='ok': failed.append(name)
    metrics={
        'v368_mainline_windows': table_count(root/'outputs/v368/m368_mainline_consolidated_final.db','mainline_trace_full'),
        'v368_transition_edges': table_count(root/'outputs/v368/m368_mainline_consolidated_final.db','mainline_transition_edge'),
        'v367_native_anchor_facts': table_count(root/'outputs/v367/m367_1_native_anchor_hardening.db','v367_native_anchor_fact'),
        'v367_rmi_default_index': table_count(root/'outputs/v367/m367_4_rmi_default_index_regression.db','v3674_rmi_hash_index'),
        'v370_runtime_samples': table_count(root/'outputs/v370/m370_native_runtime_prototype.db','v370_sample_selection'),
        'v370_stage_traces': table_count(root/'outputs/v370/m370_native_runtime_prototype.db','v370_stage_trace'),
    }
    print('metrics:', json.dumps(metrics, ensure_ascii=False, indent=2))
    nested=[]
    for p in root.rglob('*'):
        if p.is_file() and (p.name.endswith('.tar.zst') or p.name.endswith('.zip')):
            nested.append(str(p.relative_to(root)))
    print('nested compressed files:', len(nested))
    if nested:
        for x in nested[:20]: print(' nested:', x)
        failed.append('nested_compressed_files_present')
    if failed:
        print('FAILED:', ', '.join(failed))
        sys.exit(1)
    print('PASS flat complete checks')
if __name__=='__main__': main()
