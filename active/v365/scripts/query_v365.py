#!/usr/bin/env python3
import argparse, sqlite3, json
p=argparse.ArgumentParser()
p.add_argument('--db',default='outputs/m365.db')
p.add_argument('--carrier-id')
p.add_argument('--envelope-ref')
p.add_argument('--readout-id')
p.add_argument('--audit',action='store_true')
p.add_argument('--limit',type=int,default=5)
args=p.parse_args()
con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
def show(title, rows):
    print('\n## '+title)
    for r in rows:
        print(json.dumps(dict(r), ensure_ascii=False, indent=2))
if args.carrier_id:
    show('Xin carrier', cur.execute('select * from v365_xin_minimal_carrier_state where xin_carrier_id=?',(args.carrier_id,)).fetchall())
    show('External readout results', cur.execute('select * from v365_external_semantic_readout_result where readout_target_ref=? limit ?',(args.carrier_id,args.limit)).fetchall())
elif args.envelope_ref:
    show('Envelope', cur.execute('select * from v365_external_real_input_envelope_binding where envelope_ref=?',(args.envelope_ref,)).fetchall())
    show('Linked carriers', cur.execute('select * from v365_xin_minimal_carrier_state where envelope_ref=? limit ?',(args.envelope_ref,args.limit)).fetchall())
elif args.readout_id:
    show('Readout', cur.execute('select * from v365_external_semantic_readout_result where readout_id=?',(args.readout_id,)).fetchall())
elif args.audit:
    show('Semantic contamination audit', cur.execute('select * from v365_semantic_contamination_audit order by blocking desc, audit_id limit ?',(args.limit,)).fetchall())
    show('Backwrite block events', cur.execute('select * from v365_readout_backwrite_block_event order by block_event_id limit ?',(args.limit,)).fetchall())
else:
    show('Run manifest', cur.execute('select * from v365_run_manifest').fetchall())
    show('Acceptance', cur.execute('select * from v365_acceptance_report order by check_id').fetchall())
    show('Carrier sample', cur.execute('select xin_carrier_id, source_xi_ref, source_window_id, residual_mass_proxy, envelope_ref, external_definition_ref, reentry_policy_ref, carrier_status from v365_xin_minimal_carrier_state order by residual_mass_proxy desc limit ?',(args.limit,)).fetchall())
