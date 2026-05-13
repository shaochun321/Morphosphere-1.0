-- v37421: Variational EM + Closed-Loop Hebbian + Motion-PRX Integration

CREATE TABLE IF NOT EXISTS v37421_em_iteration_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    iteration INTEGER,
    j_total REAL,
    delta_j REAL,
    lambda_l REAL,
    lambda_c REAL,
    lambda_h REAL,
    lambda_b REAL,
    w_motion REAL,
    w_prx REAL,
    w_xin_cons REAL,
    w_r_core REAL,
    w_p_band REAL,
    converged INTEGER DEFAULT 0,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS v37421_em_converged_params (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    total_iterations INTEGER,
    final_j REAL,
    converged INTEGER DEFAULT 0,
    lambda_l REAL,
    lambda_c REAL,
    lambda_h REAL,
    lambda_b REAL,
    w_motion REAL,
    w_prx REAL,
    w_xin_cons REAL,
    w_r_core REAL,
    w_p_band REAL,
    params_json TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS v37421_hebbian_reward_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    round_number INTEGER,
    reward_signal REAL,
    delta_j REAL,
    motion_accuracy REAL,
    avg_weight_change REAL,
    reward_direction TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS v37421_motion_prx_coupling (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    window_k INTEGER,
    adapter_name TEXT,
    detected_regime TEXT,
    regime_confidence REAL,
    p_core_score REAL,
    p_band_score REAL,
    r_core_score REAL,
    r_band_score REAL,
    m_band_score REAL,
    x_true_score REAL,
    u_score REAL,
    created_at TEXT
);
