-- Migration: 017_v367_hardening.sql
-- v36.7.1-v36.7.5: Native Anchor Hardening + Safe Stress Guard + Semantic Quarantine + RMI Index + Release Gate
-- This is additive. No legacy DB mutation. No destructive migration.

-- ═══ v36.7.1: Native Anchor Hardening ═══

CREATE TABLE IF NOT EXISTS v367_native_anchor_fact (
    anchor_id                TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    source_adapter_id        TEXT DEFAULT NULL,
    -- Anchor bindings
    information_point_ref    TEXT NOT NULL,
    trajectory_window_ref    TEXT NOT NULL,
    evidence_bundle_ref      TEXT NOT NULL,
    coordinate_transform_ref TEXT DEFAULT NULL,
    pr_hypothesis_ref        TEXT DEFAULT NULL,
    xi_carrier_ref           TEXT DEFAULT NULL,
    ledger_ref               TEXT DEFAULT NULL,
    dark_grid_zone_ref       TEXT DEFAULT NULL,
    provenance_hash          TEXT NOT NULL DEFAULT '',
    -- Legacy compatibility
    direct_fk_available      INTEGER DEFAULT 1,
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS v367_anchor_validation_result (
    validation_id            TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    anchor_id                TEXT NOT NULL,
    information_point_hit    INTEGER DEFAULT 0,
    trajectory_window_hit    INTEGER DEFAULT 0,
    evidence_bundle_hit      INTEGER DEFAULT 0,
    ledger_hit               INTEGER DEFAULT 0,
    coordinate_invariance_ok INTEGER DEFAULT 0,
    overall_verdict          TEXT NOT NULL DEFAULT 'PENDING',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (anchor_id) REFERENCES v367_native_anchor_fact(anchor_id)
);

-- ═══ v36.7.2: Safe Stress Envelope Runtime Config ═══

CREATE TABLE IF NOT EXISTS v3672_safe_stress_envelope_rule (
    rule_id                  TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    stress_category          TEXT NOT NULL,  -- 'P_core', 'P_boundary', 'outside_support'
    intensity_level          TEXT NOT NULL,  -- 'low', 'medium', 'high', 'collapse_prone', 'failure'
    guard_action             TEXT NOT NULL,  -- 'ALLOW', 'ALLOW_WITH_AUDIT', 'AUDIT', 'DOWNSCALE', 'BLOCK_BY_DEFAULT'
    threshold_min            REAL DEFAULT 0.0,
    threshold_max            REAL DEFAULT 1.0,
    description              TEXT DEFAULT '',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS v3672_guard_action_table (
    action_id                TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    source_adapter_id        TEXT DEFAULT NULL,
    rule_id                  TEXT NOT NULL,
    triggered_by             TEXT NOT NULL DEFAULT 'system',
    input_value              REAL DEFAULT 0.0,
    resolved_action          TEXT NOT NULL DEFAULT 'AUDIT',
    outcome                  TEXT DEFAULT NULL,
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (rule_id) REFERENCES v3672_safe_stress_envelope_rule(rule_id)
);

CREATE TABLE IF NOT EXISTS v3672_guard_regression_result (
    regression_id            TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    total_rules_checked      INTEGER DEFAULT 0,
    rules_passed             INTEGER DEFAULT 0,
    coordinate_invariance_ci TEXT DEFAULT 'PENDING',
    overall_verdict          TEXT DEFAULT 'PENDING',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ v36.7.3: Semantic Quarantine Migration ═══

CREATE TABLE IF NOT EXISTS v3673_semantic_quarantine_sidecar (
    sidecar_id               TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    source_table             TEXT NOT NULL,
    source_row_id            TEXT NOT NULL,
    field_name               TEXT NOT NULL,
    quarantined_text         TEXT DEFAULT '',
    semantic_write_allowed   INTEGER DEFAULT 0,
    migration_reason         TEXT DEFAULT 'mainline_semantic_free_policy',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS v3673_mainline_semantic_free_view_manifest (
    view_id                  TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    target_table             TEXT NOT NULL,
    excluded_columns_json    TEXT NOT NULL DEFAULT '[]',
    semantic_residue_count   INTEGER DEFAULT 0,
    verdict                  TEXT NOT NULL DEFAULT 'CLEAN',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS v3673_semantic_backwrite_regression (
    regression_id            TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    attempted_backwrites     INTEGER DEFAULT 0,
    blocked_backwrites       INTEGER DEFAULT 0,
    verdict                  TEXT NOT NULL DEFAULT 'PASS',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ v36.7.4: RMI Default Index + Regression ═══

CREATE TABLE IF NOT EXISTS v3674_rmi_hash_index (
    hash_id                  TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    hash_variant             TEXT NOT NULL,  -- 'H1', 'H2', 'H3'
    source_type              TEXT NOT NULL,  -- 'spacetime_cell', 'information_fiber', 'transport_edge', 'hypothesis'
    source_id                TEXT NOT NULL,
    hash_value               TEXT NOT NULL,
    collision_group          INTEGER DEFAULT 0,
    production_use_allowed   INTEGER DEFAULT 1,
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS v3674_rmi_regression_gate (
    gate_id                  TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    h2_populated             INTEGER DEFAULT 0,
    h3_populated             INTEGER DEFAULT 0,
    h1_disabled_for_production INTEGER DEFAULT 1,
    h3_false_neighbor_groups INTEGER DEFAULT 0,
    coordinate_invariance_ci TEXT DEFAULT 'PENDING',
    inherited_gates_pass     INTEGER DEFAULT 0,
    overall_verdict          TEXT DEFAULT 'PENDING',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ v36.7.5: Consolidated Release Gate ═══

CREATE TABLE IF NOT EXISTS v367_release_gate (
    gate_id                  TEXT PRIMARY KEY,
    run_id                   TEXT NOT NULL,
    v3671_anchor_pass        INTEGER DEFAULT 0,
    v3672_guard_pass         INTEGER DEFAULT 0,
    v3673_quarantine_pass    INTEGER DEFAULT 0,
    v3674_rmi_pass           INTEGER DEFAULT 0,
    legacy_db_mutated        INTEGER DEFAULT 0,
    online_native_claimed    INTEGER DEFAULT 0,
    overall_verdict          TEXT NOT NULL DEFAULT 'PENDING',
    release_notes            TEXT DEFAULT '',
    created_at               TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);
