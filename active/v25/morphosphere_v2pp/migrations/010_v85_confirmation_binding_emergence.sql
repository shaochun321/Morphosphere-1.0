-- Migration: 010_v85_confirmation_binding_emergence.sql
-- V8.5: P/R Confirmation Graph, Spacetime-Fiber Binding, Xi Decay,
--        Emergence Alert, Proxy Provenance

-- ═══ P1: P/R Confirmation Graph ═══

CREATE TABLE IF NOT EXISTS pr_confirmation_graph_record (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,
    hypothesis_type TEXT NOT NULL DEFAULT 'P_candidate',
    current_node TEXT NOT NULL DEFAULT 'O_candidate',
    previous_node TEXT DEFAULT NULL,
    o_field_surface_id TEXT DEFAULT NULL,
    o_candidate_surface_id TEXT DEFAULT NULL,
    o_candidate_lineage_id TEXT DEFAULT NULL,
    masking_trial_count INTEGER DEFAULT 0,
    masking_support_count INTEGER DEFAULT 0,
    masking_refute_count INTEGER DEFAULT 0,
    replay_pass_count INTEGER DEFAULT 0,
    boundary_variant_count INTEGER DEFAULT 0,
    transport_support_score REAL DEFAULT 0.0,
    occupancy_persistence_length INTEGER DEFAULT 0,
    xi_pressure REAL DEFAULT 0.0,
    emergence_alert_id TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL,
    updated_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (hypothesis_id) REFERENCES object_hypothesis(hypothesis_id)
);

CREATE TABLE IF NOT EXISTS pr_graph_transition_record (
    transition_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    hypothesis_id TEXT NOT NULL,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    trigger TEXT DEFAULT 'system',
    evidence_json TEXT DEFAULT '{}',
    missing_evidence_json TEXT DEFAULT '{}',
    masking_record_ids_json TEXT DEFAULT '[]',
    verdict TEXT DEFAULT NULL,
    is_valid INTEGER DEFAULT 1,
    failure_reason TEXT DEFAULT NULL,
    reviewer TEXT DEFAULT 'system',
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (hypothesis_id) REFERENCES object_hypothesis(hypothesis_id)
);

-- ═══ P2: Xi Decay Policy ═══

CREATE TABLE IF NOT EXISTS xi_decay_policy (
    xi_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    current_state TEXT NOT NULL DEFAULT 'held',
    mass_current REAL DEFAULT 0.0,
    mass_previous REAL DEFAULT 0.0,
    decay_rate REAL DEFAULT 0.1,
    persistence_window_count INTEGER DEFAULT 0,
    relation_support_score REAL DEFAULT 0.0,
    occupancy_support_score REAL DEFAULT 0.0,
    carryover_allowed INTEGER DEFAULT 1,
    discard_after_audit_allowed INTEGER DEFAULT 0,
    audit_reason TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (xi_id) REFERENCES xi_residue_record(residue_id),
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P3: Spacetime-Fiber Binding ═══

CREATE TABLE IF NOT EXISTS spacetime_fiber_binding (
    binding_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    clock_n INTEGER DEFAULT 0,
    window_id TEXT NOT NULL,
    spacetime_cell_id TEXT NOT NULL,
    information_fiber_id TEXT NOT NULL,
    source_cell_ids_json TEXT DEFAULT '[]',
    source_patch_ids_json TEXT DEFAULT '[]',
    binding_type TEXT NOT NULL DEFAULT 'direct',
    proxy_provenance_id TEXT DEFAULT NULL,
    calibration_profile TEXT DEFAULT 'default_v83',
    provenance_hash TEXT DEFAULT '',
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (spacetime_cell_id) REFERENCES spacetime_cell(cell_uid),
    FOREIGN KEY (information_fiber_id) REFERENCES information_fiber(fiber_id)
);

-- ═══ P4-P5: Emergence Alert + Raw Emergency Export ═══

CREATE TABLE IF NOT EXISTS emergence_alert (
    alert_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    alert_type TEXT NOT NULL DEFAULT 'real_emergence',
    trigger_window_start INTEGER DEFAULT 0,
    trigger_window_end INTEGER DEFAULT 0,
    related_o_candidates_json TEXT DEFAULT '[]',
    related_pr_candidates_json TEXT DEFAULT '[]',
    related_xi_ids_json TEXT DEFAULT '[]',
    basic_conditions_json TEXT DEFAULT '[]',
    strong_trigger_conditions_json TEXT DEFAULT '[]',
    severity TEXT DEFAULT 'low',
    recommended_action TEXT DEFAULT 'no_action',
    forbidden_actions_acknowledged INTEGER DEFAULT 1,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS raw_emergency_export_manifest (
    export_id TEXT PRIMARY KEY,
    export_type TEXT NOT NULL DEFAULT 'real_emergence',
    emergence_alert_id TEXT NOT NULL,
    trigger_conditions_json TEXT DEFAULT '[]',
    run_id TEXT NOT NULL,
    window_start INTEGER DEFAULT 0,
    window_end INTEGER DEFAULT 0,
    K_scope_json TEXT DEFAULT '[0]',
    production_log_allowed INTEGER DEFAULT 0,
    scientific_use_allowed INTEGER DEFAULT 0,
    cleanup_policy TEXT DEFAULT 'archive_after_review',
    forbidden_actions_acknowledged INTEGER DEFAULT 1,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (emergence_alert_id) REFERENCES emergence_alert(alert_id)
);

-- ═══ Proxy Provenance ═══

CREATE TABLE IF NOT EXISTS proxy_provenance (
    proxy_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    target_field TEXT NOT NULL,
    proxy_type TEXT NOT NULL DEFAULT 'placeholder',
    proxy_reason TEXT DEFAULT '',
    source_assumption TEXT DEFAULT '',
    maturity_status TEXT DEFAULT 'active',
    replacement_condition TEXT DEFAULT '',
    forbidden_interpretation TEXT DEFAULT 'scientific_conclusion,final_pr_certification',
    created_by TEXT DEFAULT 'system',
    created_at TEXT DEFAULT NULL,
    review_due TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

CREATE TABLE IF NOT EXISTS proxy_density_report (
    report_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    run_type TEXT NOT NULL DEFAULT 'diagnostic_run',
    total_fields_checked INTEGER DEFAULT 0,
    proxy_fields_count INTEGER DEFAULT 0,
    proxy_density REAL DEFAULT 0.0,
    critical_path_proxy_density REAL DEFAULT 0.0,
    geometry_proxy_density REAL DEFAULT 0.0,
    transport_proxy_density REAL DEFAULT 0.0,
    pr_proxy_density REAL DEFAULT 0.0,
    ledger_proxy_density REAL DEFAULT 0.0,
    allowed_budget REAL DEFAULT 0.8,
    overload_gate_triggered INTEGER DEFAULT 0,
    downgrade_run_type_to TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ V8.5 masking_counterevidence_record extensions ═══
-- Add V8.5 fields to existing masking table (ALTER TABLE for SQLite)

-- Note: SQLite ALTER TABLE only supports ADD COLUMN, not modify.
-- These columns have defaults so existing rows are unaffected.

-- V8.5 §5.3: O-level associations
ALTER TABLE masking_counterevidence_record ADD COLUMN o_field_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN o_candidate_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN o_candidate_lineage_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN p_candidate_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN r_candidate_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN xi_candidate_id TEXT DEFAULT NULL;

-- V8.5 §5.3: Confirmation graph state tracking
ALTER TABLE masking_counterevidence_record ADD COLUMN confirmation_state_before TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN confirmation_state_after TEXT DEFAULT NULL;

-- V8.5 §5.3: Resource optimization
ALTER TABLE masking_counterevidence_record ADD COLUMN recommended_compute_tier TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN resource_saving_reason TEXT DEFAULT NULL;

-- V8.5 §5.3: Cross-references
ALTER TABLE masking_counterevidence_record ADD COLUMN ledger_alignment_report_id TEXT DEFAULT NULL;
ALTER TABLE masking_counterevidence_record ADD COLUMN emergence_alert_id TEXT DEFAULT NULL;
