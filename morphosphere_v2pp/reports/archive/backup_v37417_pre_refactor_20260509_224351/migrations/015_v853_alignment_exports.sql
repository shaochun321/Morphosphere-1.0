-- Morphosphere v8.5.3 alignment exports and threshold sweep hardening.
-- Additive diagnostic-only schema. Does not create v8.6/v9 and does not enable scientific_run.


CREATE TABLE IF NOT EXISTS threshold_sweep_record (
    sweep_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    sweep_dimension TEXT NOT NULL,
    sweep_value REAL NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    baseline_value REAL NOT NULL,
    delta_value REAL NOT NULL,
    evidence_json TEXT NOT NULL,
    forbidden_interpretation TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS failed_expectation_report (
    failure_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    expected_behavior TEXT NOT NULL,
    observed_behavior TEXT NOT NULL,
    severity TEXT NOT NULL,
    action_required TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transport_cost_matrix_record (
    record_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    base_run_id TEXT NOT NULL,
    window_from TEXT NOT NULL,
    window_to TEXT NOT NULL,
    source_uid TEXT NOT NULL,
    target_uid TEXT NOT NULL,
    geometry_cost REAL NOT NULL,
    signal_cost REAL NOT NULL,
    boundary_cost REAL NOT NULL,
    source_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    candidate_rank INTEGER NOT NULL,
    accepted INTEGER NOT NULL,
    transport_weight REAL NOT NULL,
    evidence_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xi_residue_mass_record (
    record_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    base_run_id TEXT NOT NULL,
    xi_uid TEXT NOT NULL,
    residue_type TEXT NOT NULL,
    source_failure_type TEXT NOT NULL,
    residue_mass REAL NOT NULL,
    source_hypothesis_refs_json TEXT NOT NULL,
    spatial_support_cell_uids_json TEXT NOT NULL,
    temporal_support_window_ids_json TEXT NOT NULL,
    current_state TEXT NOT NULL,
    transition_reason TEXT NOT NULL,
    created_at TEXT NOT NULL
);
