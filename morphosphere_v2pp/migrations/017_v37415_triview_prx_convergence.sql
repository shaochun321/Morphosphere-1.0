-- v37.4.15 Multi-Round Tri-View PRX Convergence Analysis tables

CREATE TABLE IF NOT EXISTS v37415_round_registry (
    round_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    formula_candidate TEXT,
    total_windows INTEGER,
    total_cells INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_prx_decomposition (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    adapter_name TEXT,
    p_core REAL NOT NULL,
    p_band REAL NOT NULL,
    r_core REAL NOT NULL,
    r_band REAL NOT NULL,
    m_band REAL NOT NULL,
    x_true REAL NOT NULL,
    u_unresolved REAL NOT NULL,
    score_p_core REAL,
    score_p_band REAL,
    score_r_core REAL,
    score_r_band REAL,
    score_m_band REAL,
    score_x_true REAL,
    score_u REAL,
    dominant_component TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_rlis_split (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    df_p_core REAL,
    df_p_band REAL,
    df_r_core REAL,
    df_r_band REAL,
    df_m_band REAL,
    df_x REAL,
    df_u REAL,
    df_total REAL,
    gamma_sync REAL,
    strict_hit INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_counter_mask_response (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    p_shield REAL,
    r_pressure REAL,
    m_tension REAL,
    r_continuity REAL,
    d_process REAL,
    r_core_indicator INTEGER,
    r_band_indicator INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_hg_fhpms_state (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    memory_p_anchor REAL,
    memory_r_band REAL,
    memory_x_random REAL,
    hebbian_strength REAL,
    hyperedge_count INTEGER,
    potential_subsidy REAL,
    fiber_measure_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_bottom_motion_constraint (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    support_drift REAL,
    kernel_change REAL,
    bandwidth_change REAL,
    motion_velocity REAL,
    fit_score REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_potential_subsidy_state (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    window_k INTEGER NOT NULL,
    phi_hebb REAL,
    phi_hyper REAL,
    phi_prx REAL,
    phi_ledger REAL,
    phi_pre_total REAL,
    f_raw REAL,
    f_effective REAL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_xin_ledger_conservation (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    x_start REAL,
    x_inflow REAL,
    x_absorbed_p REAL,
    x_resolved_r REAL,
    x_dissipated REAL,
    x_heat_bath REAL,
    x_end REAL,
    conservation_gap REAL,
    chi_x_weight REAL,
    xin_background_count INTEGER,
    xin_true_count INTEGER,
    xin_pseudo_count INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_drift_metric (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    rho_drift REAL,
    df_drift REAL,
    kernel_drift REAL,
    total_drift REAL,
    converged INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_convergence_audit (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    total_rounds INTEGER,
    final_drift REAL,
    converged INTEGER,
    true_xin_count INTEGER,
    r_core_count INTEGER,
    p_band_count INTEGER,
    unresolved_count INTEGER,
    xin_conservation_ok INTEGER,
    formula_candidate TEXT,
    verdict TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37415_round_version_manifest (
    manifest_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    schema_version TEXT,
    formula_version TEXT,
    lambda_rlis REAL,
    lambda_cm REAL,
    lambda_fhpms REAL,
    lambda_bottom REAL,
    notes TEXT,
    created_at TEXT NOT NULL
);
