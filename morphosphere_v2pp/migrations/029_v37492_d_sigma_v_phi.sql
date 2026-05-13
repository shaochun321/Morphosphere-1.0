-- v37.4.92: Internal measure time d_σ_t and motion potential velocity V_Φ(t)
-- Blueprint §4.5 (d_sigma_t) + §4.6 (V_Phi)
-- These are candidate audit metrics, NOT mainline replacements for tick.

CREATE TABLE IF NOT EXISTS d_sigma_v_phi_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine_id TEXT,
    tick INTEGER,
    phase TEXT,
    d_sigma_t REAL,
    phi_t REAL,
    phi_prev REAL,
    v_phi REAL,
    clock_delta REAL DEFAULT 1.0,
    source_delta REAL DEFAULT 0.0,
    reproj_delta REAL DEFAULT 0.0,
    phi_displacement REAL DEFAULT 0.0,
    rlis_delta REAL DEFAULT 0.0,
    churn_delta REAL DEFAULT 0.0,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_dsv_run_engine ON d_sigma_v_phi_log(run_id, engine_id);
CREATE INDEX IF NOT EXISTS idx_dsv_phase ON d_sigma_v_phi_log(phase);
