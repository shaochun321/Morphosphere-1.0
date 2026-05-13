-- v37.4.92b: V_Φ anomaly alert log (blueprint §22 risk mitigation)
-- Detects dead-node (V_Φ=0 sustained) and phase-transition (V_Φ spike) events.

CREATE TABLE IF NOT EXISTS v_phi_alert_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine_id TEXT,
    tick INTEGER,
    alert_type TEXT,
    v_phi_current REAL,
    v_phi_moving_avg REAL,
    threshold REAL,
    consecutive_zero_ticks INTEGER DEFAULT 0,
    phase TEXT,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_vpa_run ON v_phi_alert_log(run_id, alert_type);

-- d_σ_t coefficient sensitivity sweep results
CREATE TABLE IF NOT EXISTS d_sigma_sensitivity_log (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    c4_value REAL,
    d_sigma_mean REAL,
    v_phi_mean REAL,
    v_phi_max REAL,
    ticks INTEGER,
    created_at TEXT
);
