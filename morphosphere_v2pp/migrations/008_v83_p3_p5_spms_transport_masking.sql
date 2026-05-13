-- Migration: 008_v83_p3_p5_spms_transport_masking.sql
-- V8.3 P3-P5: SPMS tables, transport current edges, masking counterevidence

-- ═══ P3: SPMS Minimal Schema Bootstrap ═══

-- spacetime_cell: unified run/window/clock/node/coordinate/source/topology
CREATE TABLE IF NOT EXISTS spacetime_cell (
    cell_uid TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_k INTEGER NOT NULL DEFAULT 0,
    window_id TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    clock_start INTEGER NOT NULL DEFAULT 0,
    clock_end INTEGER NOT NULL DEFAULT 0,
    x REAL NOT NULL DEFAULT 0.0,
    y REAL NOT NULL DEFAULT 0.0,
    z REAL NOT NULL DEFAULT 0.0,
    normal_x REAL DEFAULT 0.0,
    normal_y REAL DEFAULT 0.0,
    normal_z REAL DEFAULT 1.0,
    boundary_distance REAL DEFAULT 0.0,
    support_radius REAL DEFAULT 1.0,
    source_patch_ids_json TEXT DEFAULT '[]',
    topology_neighbors_json TEXT DEFAULT '[]',
    coordinate_frame_id TEXT DEFAULT 'default',
    provenance_hash TEXT DEFAULT '',
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- information_fiber: signal state attached to spacetime cell
CREATE TABLE IF NOT EXISTS information_fiber (
    fiber_id TEXT PRIMARY KEY,
    cell_uid TEXT NOT NULL,
    V_mean REAL DEFAULT 0.0,
    V_slope REAL DEFAULT 0.0,
    release_proxy REAL DEFAULT 0.0,
    afferent_current REAL DEFAULT 0.0,
    spike_rate REAL DEFAULT 0.0,
    spike_regularity REAL DEFAULT 0.0,
    timing_precision REAL DEFAULT 0.0,
    adaptation_state REAL DEFAULT 0.0,
    signal_uncertainty REAL DEFAULT 0.0,
    compression_loss REAL DEFAULT 0.0,
    source_signal_refs_json TEXT DEFAULT '[]',
    calibration_profile TEXT DEFAULT 'default_v83',
    provenance_hash TEXT DEFAULT '',
    FOREIGN KEY (cell_uid) REFERENCES spacetime_cell(cell_uid)
);

-- transport_current_edge: per-edge transport with cost breakdown
CREATE TABLE IF NOT EXISTS transport_current_edge (
    edge_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    from_cell_uid TEXT NOT NULL,
    to_cell_uid TEXT NOT NULL,
    transport_weight REAL DEFAULT 1.0,
    current_mass REAL DEFAULT 1.0,
    geometry_cost REAL DEFAULT 0.0,
    normal_cost REAL DEFAULT 0.0,
    boundary_cost REAL DEFAULT 0.0,
    signal_cost REAL DEFAULT 0.0,
    source_patch_overlap REAL DEFAULT 0.0,
    fragility_penalty REAL DEFAULT 0.0,
    accepted INTEGER DEFAULT 1,
    transport_variant TEXT DEFAULT 'mainline',
    cycle_consistency_local REAL DEFAULT 0.0,
    boundary_crossing_penalty REAL DEFAULT 0.0,
    signal_drift REAL DEFAULT 0.0,
    gating_failure_reason TEXT DEFAULT NULL,
    provenance_hash TEXT DEFAULT '',
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (from_cell_uid) REFERENCES spacetime_cell(cell_uid),
    FOREIGN KEY (to_cell_uid) REFERENCES spacetime_cell(cell_uid)
);

-- ═══ P4: Occupancy Measure ═══

-- occupancy_measure: hypothesis occupation on spacetime cell
CREATE TABLE IF NOT EXISTS occupancy_measure (
    measure_id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    cell_uid TEXT NOT NULL,
    membership_mass REAL DEFAULT 0.0,
    membership_entropy REAL DEFAULT 0.0,
    occupancy_rank INTEGER DEFAULT 0,
    run_count INTEGER DEFAULT 1,
    window_count INTEGER DEFAULT 1,
    masking_trial_count INTEGER DEFAULT 0,
    replay_trial_count INTEGER DEFAULT 0,
    boundary_variant_count INTEGER DEFAULT 0,
    transport_support REAL DEFAULT 0.0,
    signal_support REAL DEFAULT 0.0,
    geometry_support REAL DEFAULT 0.0,
    masking_support REAL DEFAULT 0.0,
    replay_support REAL DEFAULT 0.0,
    boundary_support REAL DEFAULT 0.0,
    counterevidence_mass REAL DEFAULT 0.0,
    artifact_penalty REAL DEFAULT 0.0,
    core_margin_label TEXT DEFAULT 'unknown',
    FOREIGN KEY (hypothesis_id) REFERENCES object_hypothesis(hypothesis_id),
    FOREIGN KEY (cell_uid) REFERENCES spacetime_cell(cell_uid)
);

-- ═══ P5: Masking Counterevidence ═══

-- masking_counterevidence_record: P/R freeze hard prerequisite
CREATE TABLE IF NOT EXISTS masking_counterevidence_record (
    record_id TEXT PRIMARY KEY,
    hypothesis_id TEXT NOT NULL,
    masking_type TEXT NOT NULL DEFAULT 'random_node',
    masking_strength REAL DEFAULT 0.5,
    masked_fraction REAL DEFAULT 0.0,
    mask_specification_json TEXT DEFAULT '{}',
    base_membership_mass REAL DEFAULT 0.0,
    masked_membership_mass REAL DEFAULT 0.0,
    mass_retention REAL DEFAULT 0.0,
    classification_consistency REAL DEFAULT 0.0,
    trajectory_continuity REAL DEFAULT 0.0,
    verdict TEXT NOT NULL DEFAULT 'inconclusive',
    run_id TEXT DEFAULT NULL,
    created_at TEXT DEFAULT NULL,
    FOREIGN KEY (hypothesis_id) REFERENCES object_hypothesis(hypothesis_id)
);
