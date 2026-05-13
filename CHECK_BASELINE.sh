#!/usr/bin/env bash
set -euo pipefail
python3 - <<'INNERPY'
import sqlite3
checks=[
('v25','outputs/morphosphere_evidence_reconstruction_v25_output_database.db',[('information_point_v25',4575),('trajectory_window_trace_v25',532),('p_spacetime_measure_v25',532),('r_counter_measure_v25',532),('xi_residual_surface_v25',532)]),
('v26','outputs/morphosphere_shadow_reconstruction_v26_output_database.db',[('shadow_cell_identity_v26',86),('shadow_spacetime_cell_v26',4575),('shadow_cell_motion_state_v26',532),('shadow_graph_edge_v26',4489)]),
('v27','outputs/m27.db',[('v27_measure_point_sample',13725),('v27_measure_field_cell',13725),('v27_reversible_query_index',11278)]),
('v28','outputs/m28.db',[('v28_evidence_edge',4489),('v28_shadow_edge',4489),('v28_shadow_evidence_alignment',4489),('v28_divergence_decomposition',4489),('v28_confirmed_p_structure',4385),('v28_shadow_overreach_penalty',3783),('v28_evidence_surprise_xi',26)]),
('v29','outputs/m29.db',[('v29_intervention_proposal',389),('v29_policy_candidate',4),('v29_sandbox_replay',389),('v29_intervention_effect_report',389),('v29_action_divergence_outcome',389),('v29_precision_action_hint',109)])]
for name,db,tables in checks:
    con=sqlite3.connect(db); cur=con.cursor()
    assert cur.execute('pragma quick_check(1)').fetchone()[0]=='ok', name
    for t,n in tables:
        c=cur.execute(f'select count(*) from {t}').fetchone()[0]
        assert c==n, (name,t,c,n)
print('MORPHOSPHERE_V29_MERGED_ACCEPTANCE: PASS')
INNERPY


echo "[v30] hierarchical P renormalization"
python3 active/v30/scripts/check_v30.py --db outputs/m30.db

# v31 active inference loop check
python3 active/v31/scripts/check_v31.py --db outputs/m31.db

echo "[v32] generalized source adapter"
python3 active/v32/scripts/check_v32.py --db outputs/m32.db

echo '[v33] bottom prediction adapter'
python3 active/v33/scripts/check_v33.py --db outputs/m33.db


echo "[v34] proxy entropy control plane"
python3 active/v34/scripts/check_v34.py --db outputs/m34.db

echo "[v36.5] semantic stripping and external readout control plane"
python3 active/v365/scripts/check_v365.py --db outputs/m365.db
