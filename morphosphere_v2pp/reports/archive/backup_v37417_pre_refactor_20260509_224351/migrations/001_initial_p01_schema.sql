-- Migration: 001_initial_p01_schema.sql
-- Description: Initial schema for morphosphere V6 core objects

CREATE TABLE IF NOT EXISTS system_clock (
    clock_n INTEGER PRIMARY KEY,
    dt_seconds REAL NOT NULL DEFAULT 0.001,
    run_id TEXT NOT NULL,
    wall_clock_created_at REAL NOT NULL,
    tick_hash TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS analysis_window (
    window_id TEXT PRIMARY KEY,
    clock_start INTEGER NOT NULL,
    clock_end INTEGER NOT NULL,
    window_center INTEGER NOT NULL,
    window_size INTEGER NOT NULL,
    window_stride INTEGER NOT NULL,
    window_type TEXT DEFAULT 'standard'
);

CREATE TABLE IF NOT EXISTS cell_graph_state (
    clock_n INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL,
    num_cells INTEGER NOT NULL,
    state_json TEXT NOT NULL, -- Contains vectors like v_hair_cell
    provenance_hash TEXT DEFAULT '',
    FOREIGN KEY(clock_n) REFERENCES system_clock(clock_n)
);

CREATE TABLE IF NOT EXISTS preneural_geometry (
    node_id INTEGER PRIMARY KEY,
    patch_ids_json TEXT NOT NULL,
    position_x REAL NOT NULL,
    position_y REAL NOT NULL,
    position_z REAL NOT NULL,
    normal_x REAL NOT NULL,
    normal_y REAL NOT NULL,
    normal_z REAL NOT NULL,
    area_weight REAL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS preneural_signal_window (
    window_id TEXT NOT NULL,
    node_id INTEGER NOT NULL,
    features_json TEXT NOT NULL,
    energy_level REAL DEFAULT 0.0,
    PRIMARY KEY(window_id, node_id),
    FOREIGN KEY(window_id) REFERENCES analysis_window(window_id),
    FOREIGN KEY(node_id) REFERENCES preneural_geometry(node_id)
);

CREATE TABLE IF NOT EXISTS preneural_pointset_slice (
    slice_id TEXT PRIMARY KEY,
    window_id TEXT NOT NULL,
    geometry_node_ids_json TEXT NOT NULL,
    edges_json TEXT NOT NULL,
    signal_windows_refs_json TEXT NOT NULL,
    FOREIGN KEY(window_id) REFERENCES analysis_window(window_id)
);
