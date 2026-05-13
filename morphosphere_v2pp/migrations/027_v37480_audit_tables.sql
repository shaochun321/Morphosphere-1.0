-- v37.4.80: Blueprint §16 audit tables completion
-- promotion_decision (§16.7), ab_stress_metrics (§16.6), engine_state (§16.4)

-- §16.7: Formal promotion decision record (separate from verdict)
CREATE TABLE IF NOT EXISTS promotion_decision (
    decision_id TEXT PRIMARY KEY,
    run_id TEXT,
    candidate_engine TEXT,
    decision TEXT,           -- PROMOTE / KEEP_AS_CANDIDATE / REJECT / KEEP_A
    rationale TEXT,
    compute_overhead_pct REAL,
    holdout_metric_delta REAL,
    chaos_survival_delta REAL,
    novelty_latency_delta REAL,
    false_lockin_flag INTEGER DEFAULT 0,
    singularity_count INTEGER DEFAULT 0,
    collapse_count INTEGER DEFAULT 0,
    created_at TEXT
);

-- §16.6: Per-stream per-engine stress metrics
CREATE TABLE IF NOT EXISTS ab_stress_metrics (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine_id TEXT,
    stream_id TEXT,
    metric_name TEXT,
    metric_value REAL,
    split_role TEXT,
    generated_at TEXT
);

-- §16.4: Per-phase engine state snapshot
CREATE TABLE IF NOT EXISTS engine_state (
    record_id TEXT PRIMARY KEY,
    run_id TEXT,
    engine_id TEXT,
    phase TEXT,
    tick INTEGER,
    weight_count INTEGER,
    avg_weight REAL,
    max_weight REAL,
    entropy REAL,
    basin_depth_avg REAL,
    dead_nodes INTEGER DEFAULT 0,
    fast_state_json TEXT,
    slow_state_json TEXT,
    prior_state_json TEXT,
    created_at TEXT
);
