-- Migration: 002_p05_to_p07_schema.sql
-- Description: Schema for morphosphere V6 P05 to P07 objects

CREATE TABLE IF NOT EXISTS transport_operator (
    transport_id TEXT PRIMARY KEY,
    from_slice_id TEXT NOT NULL,
    to_slice_id TEXT NOT NULL,
    mapping_matrix_json TEXT NOT NULL,
    transport_error REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS t_surface (
    t_surface_id TEXT PRIMARY KEY,
    stage_k INTEGER NOT NULL,
    slice_ids_json TEXT NOT NULL,
    transport_ids_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS o_field_surface (
    field_id TEXT PRIMARY KEY,
    t_surface_id TEXT NOT NULL,
    field_matrix_json TEXT NOT NULL,
    FOREIGN KEY(t_surface_id) REFERENCES t_surface(t_surface_id)
);

CREATE TABLE IF NOT EXISTS o_candidate_surface (
    candidate_surface_id TEXT PRIMARY KEY,
    field_surface_id TEXT NOT NULL,
    clusters_json TEXT NOT NULL,
    FOREIGN KEY(field_surface_id) REFERENCES o_field_surface(field_id)
);

CREATE TABLE IF NOT EXISTS observable_surface (
    o_surface_id TEXT PRIMARY KEY,
    stage_k INTEGER NOT NULL,
    t_surface_id TEXT NOT NULL,
    field_surface_id TEXT NOT NULL,
    candidate_surface_id TEXT NOT NULL,
    FOREIGN KEY(t_surface_id) REFERENCES t_surface(t_surface_id),
    FOREIGN KEY(field_surface_id) REFERENCES o_field_surface(field_id),
    FOREIGN KEY(candidate_surface_id) REFERENCES o_candidate_surface(candidate_surface_id)
);

CREATE TABLE IF NOT EXISTS p_band_record (
    p_band_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    core_margin_type TEXT NOT NULL,
    member_node_ids_json TEXT NOT NULL,
    coherence_score REAL DEFAULT 0.0,
    replay_support REAL DEFAULT 0.0,
    origin_anchor_id TEXT DEFAULT '',
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);

CREATE TABLE IF NOT EXISTS r_band_record (
    r_band_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    margin_outer_type TEXT NOT NULL,
    residual_reason TEXT NOT NULL,
    routing_target TEXT DEFAULT '',
    upgrade_conditions_json TEXT NOT NULL,
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);

CREATE TABLE IF NOT EXISTS occupancy_state (
    occupancy_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    occupancy_distribution_json TEXT NOT NULL,
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);

CREATE TABLE IF NOT EXISTS origin_anchor_bundle (
    origin_id TEXT PRIMARY KEY,
    o_surface_id TEXT NOT NULL,
    supporting_p_ids_json TEXT NOT NULL,
    stability_score REAL DEFAULT 0.0,
    FOREIGN KEY(o_surface_id) REFERENCES observable_surface(o_surface_id)
);
