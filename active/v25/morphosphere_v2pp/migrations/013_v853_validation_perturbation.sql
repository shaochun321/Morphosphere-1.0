-- Morphosphere v8.5.3 Validation & Perturbation Build
-- Additive diagnostic-only schema. This migration does not create v8.6/v9 and does not enable scientific_run.

CREATE TABLE IF NOT EXISTS perturbation_run_manifest (
    perturbation_run_id TEXT PRIMARY KEY,
    base_run_id TEXT NOT NULL,
    validation_version TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    perturbation_profile TEXT NOT NULL,
    config_json TEXT NOT NULL,
    allowed_use TEXT NOT NULL,
    forbidden_use TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS perturbation_effect_report (
    effect_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    perturbation_type TEXT NOT NULL,
    target_metric TEXT NOT NULL,
    baseline_value REAL NOT NULL,
    perturbed_value REAL NOT NULL,
    delta_value REAL NOT NULL,
    expected_direction TEXT NOT NULL,
    actual_direction TEXT NOT NULL,
    passed INTEGER NOT NULL,
    evidence_json TEXT NOT NULL,
    forbidden_interpretation TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS counterfactual_acceptance_report (
    acceptance_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    check_name TEXT NOT NULL,
    expected_direction TEXT NOT NULL,
    actual_direction TEXT NOT NULL,
    passed INTEGER NOT NULL,
    diagnostic_message TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transport_cost_matrix_report (
    report_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    stage_k INTEGER NOT NULL,
    candidate_count INTEGER NOT NULL,
    mean_geometry_cost REAL NOT NULL,
    mean_signal_cost REAL NOT NULL,
    mean_boundary_cost REAL NOT NULL,
    mean_transport_weight REAL NOT NULL,
    rejected_fraction REAL NOT NULL,
    source_distribution_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS object_evidence_record (
    evidence_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    baseline_support_score REAL NOT NULL,
    perturbed_support_score REAL NOT NULL,
    evidence_terms_json TEXT NOT NULL,
    posterior_score_proxy REAL NOT NULL,
    forbidden_use TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xi_residual_mass_report (
    report_id TEXT PRIMARY KEY,
    perturbation_run_id TEXT NOT NULL,
    residue_type TEXT NOT NULL,
    baseline_residue_mass REAL NOT NULL,
    perturbed_residue_mass REAL NOT NULL,
    expected_state_pressure TEXT NOT NULL,
    source_failure_type TEXT NOT NULL,
    created_at TEXT NOT NULL
);
