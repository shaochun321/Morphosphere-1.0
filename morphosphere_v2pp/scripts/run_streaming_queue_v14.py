#!/usr/bin/env python3
"""Rebuild v1.4 acceptance/runtime sidecar from existing v1.4 DB layer.
This package already contains the append-only v1.4 tables. The script refreshes
runtime sidecar samples and report summaries from those tables without mutating
source facts or upstream v1.3 tables.
"""
import argparse, sqlite3, json, hashlib
from pathlib import Path

def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path,'w',encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--db', required=True)
    ap.add_argument('--runtime-dir', default='runtime_store/v14')
    ap.add_argument('--report-dir', default='morphosphere_v2pp/reports')
    args=ap.parse_args()
    rt=Path(args.runtime_dir); rp=Path(args.report_dir); rt.mkdir(parents=True, exist_ok=True); rp.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(args.db); con.row_factory=sqlite3.Row; cur=con.cursor()
    q=list(cur.execute('SELECT * FROM streaming_queue_event_v14 ORDER BY queue_enter_order LIMIT 120'))
    d=list(cur.execute('SELECT * FROM queue_to_sensorium_dispatch_v14 ORDER BY clock_n, dispatched_order LIMIT 120'))
    ticks=list(cur.execute('SELECT * FROM streaming_queue_tick_state_v14 ORDER BY clock_n'))
    resp=list(cur.execute('SELECT * FROM queue_pr_xi_response_v14 ORDER BY clock_n, trajectory_id'))
    event_count=cur.execute('SELECT COUNT(*) FROM streaming_queue_event_v14').fetchone()[0]
    dispatch_count=cur.execute('SELECT COUNT(*) FROM queue_to_sensorium_dispatch_v14').fetchone()[0]
    drop_count=cur.execute("SELECT COUNT(*) FROM streaming_queue_event_v14 WHERE queue_status='dropped'").fetchone()[0]
    avg_latency=cur.execute('SELECT AVG(latency_ms) FROM streaming_queue_event_v14 WHERE latency_ms IS NOT NULL').fetchone()[0] or 0
    base_p=cur.execute('SELECT AVG(p_stability_proxy) FROM queue_pr_xi_response_v14').fetchone()[0] or 0
    base_x=cur.execute('SELECT AVG(xi_pressure_proxy) FROM queue_pr_xi_response_v14').fetchone()[0] or 0
    write_json(rt/'streaming_queue_manifest_v14.json', {'version':'v1.4','event_count':event_count,'dispatch_count':dispatch_count,'drop_count':drop_count,'boundary':'runtime sidecar; sqlite ledger only'})
    write_jsonl(rt/'queue_event_sample_v14.jsonl', [dict(x) for x in q])
    write_jsonl(rt/'queue_dispatch_sample_v14.jsonl', [dict(x) for x in d])
    write_jsonl(rt/'backpressure_tick_state_v14.jsonl', [dict(x) for x in ticks])
    write_jsonl(rt/'queue_pr_xi_response_v14.jsonl', [dict(x) for x in resp])
    report=f'# Streaming Queue + Backpressure Runtime v1.4\n\nqueue_events={event_count}\ndispatched={dispatch_count}\ndropped={drop_count}\navg_latency_ms={avg_latency:.6f}\nbase_p={base_p:.6f}\nbase_xi={base_x:.6f}\n'
    (rp/'STREAMING_QUEUE_BACKPRESSURE_V14_REPORT.md').write_text(report, encoding='utf-8')
    write_json(rp/'streaming_queue_v14_summary.json', {'version':'v1.4','queue_events':event_count,'dispatched':dispatch_count,'dropped':drop_count,'baseline_p':base_p,'baseline_xi':base_x,'avg_latency_ms':avg_latency})
    con.close()
    print('streaming_queue_v1.4 sidecars refreshed')
if __name__=='__main__': main()
