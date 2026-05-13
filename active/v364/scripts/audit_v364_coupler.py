#!/usr/bin/env python3
import argparse, sqlite3
ap=argparse.ArgumentParser()
ap.add_argument('--db', default='outputs/m364.db')
args=ap.parse_args()
con=sqlite3.connect(args.db)
selected=con.execute('SELECT COUNT(*) FROM v364_variational_coupling_cost WHERE selected=1').fetchone()[0]
high_risk=con.execute("SELECT COUNT(*) FROM v364_pseudo_continuity_score WHERE pseudo_continuity_risk='high'").fetchone()[0]
fg=con.execute("SELECT COUNT(*) FROM v364_xin_triage_policy WHERE triage_class='foreground'").fetchone()[0]
thermal=con.execute("SELECT COUNT(*) FROM v364_xin_triage_policy WHERE triage_class='thermalized'").fetchone()[0]
loss=con.execute('SELECT COUNT(*) FROM v364_cognitive_field_residual_audit WHERE used_as_loss!=0').fetchone()[0]
print('selected_bands', selected)
print('high_pseudo_continuity_risk', high_risk)
print('foreground_xin', fg)
print('thermalized_xin', thermal)
print('field_residual_used_as_loss', loss)
print('PASS coupler audit' if selected>0 and loss==0 else 'FAIL coupler audit')
con.close()
