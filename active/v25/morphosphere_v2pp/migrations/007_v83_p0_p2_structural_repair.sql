-- Migration: 007_v83_p0_clock_repair.sql
-- V8.3 P0: Contract + Clock Repair
-- Establishes run_manifest and system_clock as authoritative sources.

-- run_manifest: fixes run identity, version, calibration for all downstream objects
CREATE TABLE IF NOT EXISTS run_manifest (
    run_id TEXT PRIMARY KEY,
    rules_version TEXT NOT NULL DEFAULT 'v8.3',
    schema_version TEXT NOT NULL DEFAULT 'v8.3',
    calibration_profile TEXT NOT NULL DEFAULT 'default_v83',
    execution_mode TEXT NOT NULL DEFAULT 'diagnostic',
    input_source TEXT DEFAULT NULL,
    cell_count INTEGER DEFAULT 0,
    window_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    notes TEXT DEFAULT NULL
);

-- system_clock: canonical time index, cell_graph_state.clock_n must reference here
CREATE TABLE IF NOT EXISTS system_clock_entry (
    clock_n INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    time_s REAL NOT NULL DEFAULT 0.0,
    dt_s REAL NOT NULL DEFAULT 0.001,
    clock_hash TEXT DEFAULT '',
    schema_version TEXT NOT NULL DEFAULT 'v8.3',
    PRIMARY KEY (run_id, clock_n),
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- V8.3 P1: solver_diagnostics maturity gate
ALTER TABLE solver_diagnostics ADD COLUMN maturity_gate_passed INTEGER DEFAULT 0;
ALTER TABLE solver_diagnostics ADD COLUMN solver_convergence_detail TEXT DEFAULT NULL;

-- V8.3 P2: o_candidate_surface formal table (v8.1-T3 + v8.3 §3.5)
CREATE TABLE IF NOT EXISTS o_candidate_record (
    candidate_id TEXT PRIMARY KEY,
    candidate_type TEXT NOT NULL DEFAULT 'candidate_p',  -- candidate_p/candidate_r/candidate_origin/candidate_boundary/candidate_xi
    stage_k INTEGER NOT NULL,
    field_surface_id TEXT NOT NULL,
    o_surface_id TEXT DEFAULT NULL,
    member_node_ids_json TEXT NOT NULL DEFAULT '[]',
    support_score REAL DEFAULT 0.0,
    transport_support_score REAL DEFAULT 0.0,
    replay_support_score REAL DEFAULT 0.0,
    boundary_penalty REAL DEFAULT 0.0,
    solver_converged INTEGER DEFAULT 0,
    maturity_flag TEXT NOT NULL DEFAULT 'scaffold',  -- scaffold/candidate/freezable/frozen
    source_hypothesis_id TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL
);

-- V8.3 P3: object_hypothesis (SPMS §5.5)
CREATE TABLE IF NOT EXISTS object_hypothesis (
    hypothesis_id TEXT PRIMARY KEY,
    hypothesis_type TEXT NOT NULL DEFAULT 'P_candidate',  -- P_candidate/R_candidate/origin_candidate/boundary_candidate/proto_structure/xi_proto/refuted_candidate
    stage_k INTEGER NOT NULL,
    run_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate',  -- candidate/provisional/masked_validated/frozen/certified/refuted/suspended
    member_cell_uids_json TEXT NOT NULL DEFAULT '[]',
    spatial_support_json TEXT DEFAULT NULL,
    temporal_support_json TEXT DEFAULT NULL,
    support_score REAL DEFAULT 0.0,
    competition_set_id TEXT DEFAULT NULL,
    source_candidate_id TEXT DEFAULT NULL,
    source_decomposition_ref TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- V8.3: t_surface transport mode (v8.1-T5)
ALTER TABLE t_surface ADD COLUMN transport_mode TEXT DEFAULT 'connected';
