-- Morphosphere V7: Noether-Entropy External Ledger and Transformation Records

CREATE TABLE IF NOT EXISTS transformation_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    transform_id TEXT NOT NULL,
    domain_object_refs JSON NOT NULL,
    codomain_object_refs JSON NOT NULL,
    loss_metrics JSON NOT NULL,
    unit_policy_followed BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS external_conserved_quantity_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    symmetry_id TEXT NOT NULL,
    quantity_name TEXT NOT NULL,
    ledger_value_before REAL NOT NULL,
    ledger_value_after REAL NOT NULL,
    source_term REAL NOT NULL,
    dissipation_term REAL NOT NULL,
    anomaly_term REAL NOT NULL,
    balance_residual REAL NOT NULL,
    evidence_ref TEXT,
    linked_object_refs JSON
);

CREATE TABLE IF NOT EXISTS external_entropy_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    transport_entropy REAL NOT NULL,
    candidate_fragment_entropy REAL NOT NULL,
    origin_support_entropy REAL NOT NULL,
    residual_accumulation_entropy REAL NOT NULL,
    external_entropy_total REAL NOT NULL,
    calculation_variant TEXT NOT NULL,
    evidence_ref TEXT,
    transport_ref TEXT
);

CREATE TABLE IF NOT EXISTS external_noise_budget_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    noise_budget_ext REAL NOT NULL,
    noise_budget_measurement REAL NOT NULL,
    noise_budget_windowing REAL NOT NULL,
    noise_budget_transport REAL NOT NULL,
    noise_budget_boundary REAL NOT NULL,
    noise_budget_total REAL NOT NULL,
    noise_source_manifest TEXT,
    budget_unit_policy TEXT DEFAULT 'ledger_unit'
);

CREATE TABLE IF NOT EXISTS external_dissipation_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    coarse_graining_dissipation REAL NOT NULL,
    boundary_dissipation REAL NOT NULL,
    numerical_dissipation REAL NOT NULL,
    dissipation_total REAL NOT NULL,
    evidence_ref TEXT,
    dissipation_variant TEXT DEFAULT 'v1_minimal'
);

CREATE TABLE IF NOT EXISTS external_anomaly_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL,
    anomaly_score REAL NOT NULL,
    possible_sources JSON,
    linked_object_refs JSON,
    evidence_ref TEXT
);

CREATE TABLE IF NOT EXISTS external_isolation_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_version TEXT NOT NULL,
    run_id TEXT NOT NULL,
    stage_k_id TEXT NOT NULL,
    window_id TEXT NOT NULL,
    related_T_ref TEXT,
    related_O_ref TEXT,
    related_P_refs JSON,
    related_R_refs JSON,
    related_origin_ref TEXT,
    external_free_energy REAL NOT NULL,
    balance_summary TEXT NOT NULL,
    recommended_validation_path TEXT,
    linked_ledger_refs JSON
);
