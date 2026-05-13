-- Migration: 012_v852_execution_fidelity.sql
-- V8.5.2 diagnostic-only execution fidelity additions.
-- No v8.6/v9 schema boundary. No scientific_run semantics.

ALTER TABLE o_candidate_record ADD COLUMN formation_mode TEXT DEFAULT 'pass_through_proxy';
ALTER TABLE o_candidate_record ADD COLUMN metadata_json TEXT DEFAULT '{}';
ALTER TABLE relation_entropy_record ADD COLUMN entropy_source_distribution TEXT DEFAULT '[]';

CREATE TABLE IF NOT EXISTS transport_gating_failure_report (
    failure_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    from_cell_uid TEXT NOT NULL,
    to_cell_uid TEXT NOT NULL,
    total_cost REAL DEFAULT 0.0,
    theta_transport REAL DEFAULT 0.0,
    reason TEXT DEFAULT '',
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS diagnostic_telemetry_report (
    report_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    total_rows_written INTEGER DEFAULT 0,
    rows_by_table_json TEXT DEFAULT '{}',
    write_amplification_ratio REAL DEFAULT 0.0,
    masking_cost_ms REAL DEFAULT 0.0,
    confirmation_update_cost_ms REAL DEFAULT 0.0,
    transport_cost_ms REAL DEFAULT 0.0,
    export_bundle_size_bytes INTEGER DEFAULT 0,
    hot_path_cost_estimate TEXT DEFAULT '',
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);
