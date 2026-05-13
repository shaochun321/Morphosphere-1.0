-- Migration: 003_p08_to_p10_schema.sql
-- Description: Schema for morphosphere V6 P08 to P10 objects

CREATE TABLE IF NOT EXISTS boundary_elasticity_record (
    boundary_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    elasticity_score REAL NOT NULL,
    elasticity_type TEXT DEFAULT 'standard',
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);

CREATE TABLE IF NOT EXISTS other_boundary_separation_record (
    relation_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    separation_distance REAL NOT NULL,
    relation_type TEXT DEFAULT 'unknown',
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);

CREATE TABLE IF NOT EXISTS recursive_transition_record (
    transition_id TEXT PRIMARY KEY,
    from_stage_k INTEGER NOT NULL,
    to_stage_kplus1 INTEGER NOT NULL,
    source_p_ids_json TEXT NOT NULL,
    triggering_r_ids_json TEXT NOT NULL,
    origin_id TEXT NOT NULL,
    seed_id TEXT NOT NULL,
    transition_confidence REAL DEFAULT 0.0,
    continuity_score REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS t_seed_replay_packet (
    seed_id TEXT PRIMARY KEY,
    transition_id TEXT NOT NULL,
    source_p_ids_json TEXT NOT NULL,
    allowed_drive_envelope TEXT DEFAULT '',
    expected_region TEXT DEFAULT '',
    FOREIGN KEY(transition_id) REFERENCES recursive_transition_record(transition_id)
);

CREATE TABLE IF NOT EXISTS family_recursive_surface_index (
    surface_id TEXT PRIMARY KEY,
    clock_n INTEGER NOT NULL,
    transition_ids_json TEXT NOT NULL,
    shell0_verdict TEXT DEFAULT 'unknown'
);

CREATE TABLE IF NOT EXISTS semantic_readout_surface (
    readout_id TEXT PRIMARY KEY,
    surface_id TEXT NOT NULL,
    dominant_family_label TEXT NOT NULL,
    onset_category TEXT DEFAULT 'unknown',
    readout_confidence REAL DEFAULT 0.0,
    FOREIGN KEY(surface_id) REFERENCES family_recursive_surface_index(surface_id)
);
