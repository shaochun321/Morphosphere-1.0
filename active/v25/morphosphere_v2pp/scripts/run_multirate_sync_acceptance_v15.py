#!/usr/bin/env python3
import argparse, sqlite3, sys

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('db'); args=ap.parse_args()
    con=sqlite3.connect(args.db); cur=con.cursor()
    checks=[]
    def chk(name, cond, detail=''):
        checks.append((name, bool(cond), detail))
    def count(t): return cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    chk('sqlite_quick_check', cur.execute('PRAGMA quick_check').fetchone()[0]=='ok')
    chk('clock_domains', count('clock_domain_registry_v15')>=6, str(count('clock_domain_registry_v15')))
    chk('sensor_samples', count('multirate_sensor_sample_v15')>100, str(count('multirate_sensor_sample_v15')))
    chk('sync_frames', count('resampled_sync_frame_v15')==10, str(count('resampled_sync_frame_v15')))
    chk('cross_modal_bindings', count('cross_modal_binding_v15')==50, str(count('cross_modal_binding_v15')))
    chk('fused_events', count('fused_sensor_event_v15')==50, str(count('fused_sensor_event_v15')))
    chk('fusion_pr_xi', count('fusion_pr_xi_response_v15')==50, str(count('fusion_pr_xi_response_v15')))
    base=cur.execute("SELECT xi_pressure_proxy FROM multirate_replay_result_v15 WHERE scenario_id='baseline_multirate_sync'").fetchone()[0]
    jitter=cur.execute("SELECT xi_pressure_proxy FROM multirate_replay_result_v15 WHERE scenario_id='clock_jitter_20ms'").fetchone()[0]
    chk('jitter_raises_xi', jitter>base, f'{jitter}>{base}')
    lag_r=cur.execute("SELECT r_counter_proxy FROM multirate_replay_result_v15 WHERE scenario_id='acoustic_phase_lag'").fetchone()[0]
    base_r=cur.execute("SELECT r_counter_proxy FROM multirate_replay_result_v15 WHERE scenario_id='baseline_multirate_sync'").fetchone()[0]
    chk('phase_lag_raises_r', lag_r>base_r, f'{lag_r}>{base_r}')
    chk('hot_swap_forbidden_contract', cur.execute("SELECT allowed FROM runtime_sync_boundary_contract_v15 WHERE contract_id='hot_swap_forbidden'").fetchone()[0]==1)
    chk('p_r_before_xi_contract', cur.execute("SELECT allowed FROM runtime_sync_boundary_contract_v15 WHERE contract_id='p_r_before_xi'").fetchone()[0]==1)
    failed=[c for c in checks if not c[1]]
    for n,ok,d in checks: print(('PASS' if ok else 'FAIL'), n, d)
    print(f'multirate_sync_v1.5 acceptance: {len(checks)-len(failed)} / {len(checks)} PASS')
    con.close()
    if failed: sys.exit(1)
if __name__=='__main__': main()
