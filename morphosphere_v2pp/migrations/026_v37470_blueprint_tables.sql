-- Migration 026: Blueprint 2026.5.10.1 §16 tables
-- source_event (§16.1), measure_coordinate (§16.3), topological_inertia_event (§16.5)

-- §16.1: Source Event — minimum external data provenance
CREATE TABLE IF NOT EXISTS source_event (
    event_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    split_role TEXT NOT NULL DEFAULT 'calibration',  -- calibration|validation|holdout|live
    event_time TEXT NOT NULL,
    payload_hash TEXT NOT NULL DEFAULT '',
    raw_ref TEXT DEFAULT '',
    external_real_data INTEGER NOT NULL DEFAULT 0,   -- 1=external, 0=synthetic/fixture
    source_url TEXT DEFAULT '',
    license_or_policy TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

-- §16.3: Measure Coordinate — non-semantic 7-dim z_t vector
CREATE TABLE IF NOT EXISTS measure_coordinate (
    record_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    transition_cost REAL NOT NULL DEFAULT 0.0,
    drift_cost REAL NOT NULL DEFAULT 0.0,
    gamma_desync_cost REAL NOT NULL DEFAULT 0.0,
    xin_residual_cost REAL NOT NULL DEFAULT 0.0,
    potential_displacement_cost REAL NOT NULL DEFAULT 0.0,
    cross_slice_churn_cost REAL NOT NULL DEFAULT 0.0,
    magnitude_disturbance_cost REAL NOT NULL DEFAULT 0.0,
    semantic_leakage_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

-- §16.5: Topological Inertia Event — per-event M_eff audit trail
CREATE TABLE IF NOT EXISTS topological_inertia_event (
    record_id TEXT PRIMARY KEY,
    engine_id TEXT NOT NULL,
    tick INTEGER NOT NULL,
    event_id TEXT NOT NULL DEFAULT '',
    class_id TEXT NOT NULL DEFAULT '',
    from_entity TEXT NOT NULL DEFAULT '',
    to_entity TEXT NOT NULL DEFAULT '',
    phi REAL NOT NULL DEFAULT 0.0,
    m_eff REAL NOT NULL DEFAULT 0.0,
    delta_w REAL NOT NULL DEFAULT 0.0,
    external_hits INTEGER NOT NULL DEFAULT 0,
    internal_only_hits INTEGER NOT NULL DEFAULT 0,
    recent_xin_residual REAL NOT NULL DEFAULT 0.0,
    contradiction_penalty REAL NOT NULL DEFAULT 0.0,
    a_t_gate REAL NOT NULL DEFAULT 1.0,
    mass_clipped INTEGER NOT NULL DEFAULT 0,
    singularity_flag INTEGER NOT NULL DEFAULT 0,
    collapse_flag INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
