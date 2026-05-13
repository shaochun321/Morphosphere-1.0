-- v37.4.90: §16.2 process_window + §13.3 self_reference_event

-- §16.2: Process window records (event → window mapping)
CREATE TABLE IF NOT EXISTS process_window (
    window_id TEXT PRIMARY KEY,
    event_id TEXT,
    origin_anchor TEXT,
    reprojection_hash TEXT,
    cell_count INTEGER DEFAULT 0,
    window_duration_ticks INTEGER DEFAULT 0,
    created_at TEXT
);

-- §13.3: Self-reference audit events (7 required fields)
CREATE TABLE IF NOT EXISTS self_reference_event (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    self_reference_event_id TEXT,
    engine_id TEXT,
    internal_state_dependencies TEXT,
    external_event_dependency TEXT,
    external_hit_count INTEGER DEFAULT 0,
    internal_only_activation_count INTEGER DEFAULT 0,
    rlis_sync_state TEXT,
    xin_residual_state REAL DEFAULT 0.0,
    tick INTEGER,
    created_at TEXT
);
