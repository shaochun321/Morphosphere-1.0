#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path
base=Path(__file__).resolve().parent
if len(sys.argv)<2:
    print("usage: query_v366_pass17.py [summary|anchors|calibration|ctc02|semantic]"); sys.exit(1)
cmd=sys.argv[1]
def show(db,sql):
    con=sqlite3.connect(base/db); con.row_factory=sqlite3.Row
    for r in con.execute(sql): print(dict(r))
    con.close()
if cmd=="summary": show("m366_pass17_hardening_summary.db","select * from pass17_summary_metric")
elif cmd=="anchors": show("m366_pass17_backprojection_hardening.db","select * from pass17_backprojection_hardening_summary")
elif cmd=="calibration": show("m366_pass17_source_rerun_calibration.db","select * from pass17_safe_pressure_interval limit 20")
elif cmd=="ctc02": show("m366_pass17_ctc02_upper_overlay.db","select * from pass17_comparison_01_02_upper_layer")
elif cmd=="semantic": show("m366_pass17_semantic_payload_audit.db","select * from pass17_semantic_payload_summary")
else: print("unknown command")
