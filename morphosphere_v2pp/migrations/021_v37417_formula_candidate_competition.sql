-- v37.4.17 Formula Candidate Competition tables

CREATE TABLE IF NOT EXISTS v37417_formula_candidate_registry (
    candidate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    candidate_code TEXT NOT NULL,
    candidate_name TEXT NOT NULL,
    lambda_rlis REAL, lambda_cm REAL, lambda_fhpms REAL, lambda_bottom REAL, lambda_math REAL,
    description TEXT, created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37417_round_candidate_evaluation (
    eval_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    candidate_code TEXT NOT NULL,
    j_motion_fit REAL, j_prx_stability REAL, j_xin_conservation REAL,
    j_r_core REAL, j_p_band REAL,
    j_unresolved REAL, j_drift REAL, j_writeback_risk REAL,
    j_total REAL,
    p_core_avg REAL, p_band_avg REAL, r_core_avg REAL, r_band_avg REAL,
    m_band_avg REAL, x_true_avg REAL, u_avg REAL,
    selected INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37417_round_selection_history (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    selected_candidate TEXT NOT NULL,
    j_total_selected REAL,
    runner_up_candidate TEXT,
    j_total_runner_up REAL,
    margin REAL,
    selection_reason TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37417_candidate_drift_analysis (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    round_number INTEGER NOT NULL,
    candidate_code TEXT NOT NULL,
    rho_drift_from_prev REAL,
    j_total_change REAL,
    rank_change INTEGER,
    prev_rank INTEGER,
    curr_rank INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v37417_formula_evolution_summary (
    summary_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    total_rounds INTEGER,
    final_winner TEXT,
    winner_stability_pct REAL,
    rank_volatility REAL,
    convergence_round INTEGER,
    formula_switches INTEGER,
    verdict TEXT,
    analysis_json TEXT,
    created_at TEXT NOT NULL
);
