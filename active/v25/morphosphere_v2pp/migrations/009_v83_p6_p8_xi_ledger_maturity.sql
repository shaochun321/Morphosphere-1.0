-- Migration: 009_v83_p6_p8_xi_ledger_maturity.sql
-- V8.3 P6-P8: Xi residue, relation ledger, maturity gate

-- ═══ P6: Xi Residue Carrier ═══

CREATE TABLE IF NOT EXISTS xi_residue_record (
    residue_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_k INTEGER NOT NULL DEFAULT 0,
    source_o_surface_id TEXT DEFAULT NULL,
    source_hypothesis_refs_json TEXT DEFAULT '[]',
    residue_norm REAL DEFAULT 0.0,
    residue_mass REAL DEFAULT 0.0,
    residue_entropy_proxy REAL DEFAULT 0.0,
    spatial_support_cell_uids_json TEXT DEFAULT '[]',
    temporal_support_window_ids_json TEXT DEFAULT '[]',
    residue_type TEXT NOT NULL DEFAULT 'unknown',
    carry_mode TEXT NOT NULL DEFAULT 'carry',
    decay_rate REAL DEFAULT 0.1,
    memory_depth INTEGER DEFAULT 1,
    carry_weight REAL DEFAULT 1.0,
    promotion_conditions_json TEXT DEFAULT NULL,
    quarantine_conditions_json TEXT DEFAULT NULL,
    linked_noise_budget_ref TEXT DEFAULT NULL,
    linked_anomaly_ref TEXT DEFAULT NULL,
    linked_entropy_ref TEXT DEFAULT NULL,
    linked_solver_diagnostic_ref TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P6: Relation Entropy Record ═══

CREATE TABLE IF NOT EXISTS relation_entropy_record (
    record_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    relation_type TEXT NOT NULL DEFAULT 'transport_entropy',
    subject_group TEXT NOT NULL DEFAULT '',
    object_group TEXT NOT NULL DEFAULT '',
    support_cells_json TEXT DEFAULT '[]',
    support_windows_json TEXT DEFAULT '[]',
    entropy_value REAL DEFAULT 0.0,
    normalized_entropy REAL DEFAULT 0.0,
    effective_sample_size INTEGER DEFAULT 0,
    calibration_profile TEXT DEFAULT 'default_v83',
    allowed_use TEXT DEFAULT 'audit,diagnostic,comparison',
    forbidden_use TEXT DEFAULT 'freeze_pr,select_omega,generate_tseed,mainline_truth',
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P7: Maturity Gate Record ═══

CREATE TABLE IF NOT EXISTS maturity_gate_record (
    gate_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    target_object_type TEXT NOT NULL DEFAULT 'P_candidate',
    target_ref TEXT NOT NULL,
    from_status TEXT NOT NULL DEFAULT 'candidate',
    to_status TEXT NOT NULL DEFAULT 'provisional',
    required_evidence_json TEXT DEFAULT '{}',
    provided_evidence_json TEXT DEFAULT '{}',
    missing_evidence_json TEXT DEFAULT '{}',
    gate_result TEXT NOT NULL DEFAULT 'blocked',
    failure_reason TEXT DEFAULT NULL,
    reviewer TEXT DEFAULT 'system',
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);
