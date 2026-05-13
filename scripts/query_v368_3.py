#!/usr/bin/env python3
import sqlite3, sys
def main():
    db=sys.argv[1] if len(sys.argv)>1 else 'm368_3_mainline_empirical_batch.db'; cmd=sys.argv[2] if len(sys.argv)>2 else 'summary'
    con=sqlite3.connect(db); con.row_factory=sqlite3.Row
    if cmd=='summary':
        for t in ['v3683_mainline_trace_full','v3683_continuous_transition_edge','v3683_transition_summary','v3683_masking_diversion_audit','v3683_ctc_sequence_role_upper_rollup','v3683_module_contribution_decomposition','v3683_acceptance_report']:
            print(t, con.execute(f'select count(*) c from {t}').fetchone()['c'])
    elif cmd=='transitions':
        for r in con.execute('select * from v3683_transition_summary order by edge_count desc'): print(dict(r))
    elif cmd=='trace':
        tid=sys.argv[3] if len(sys.argv)>3 else None
        rows=con.execute('select * from v3683_mainline_trace_full where trajectory_trace_id=? or trace_id=?',(tid,tid)).fetchall() if tid else con.execute('select * from v3683_mainline_trace_full limit 5').fetchall()
        for r in rows: print(dict(r))
    elif cmd=='answers':
        for r in con.execute('select * from v3683_mainline_answer_matrix order by question_id'):
            print('\n'+r['question_id'], r['question']); print(r['data_answer']); print('tables:', r['supporting_tables']); print('boundary:', r['boundary'])
    else: print('commands: summary | transitions | trace [id] | answers')
    con.close()
if __name__=='__main__': main()
