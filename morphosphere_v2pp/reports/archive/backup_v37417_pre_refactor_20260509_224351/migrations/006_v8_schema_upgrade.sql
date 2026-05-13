-- Migration: 006_v8_schema_upgrade.sql
-- Description: Add V8 fields to preneural, transport, family surface, and solver tables

-- V8-T1: GeometryNode extended fields
ALTER TABLE preneural_geometry ADD COLUMN boundary_distance REAL DEFAULT 0.0;
ALTER TABLE preneural_geometry ADD COLUMN support_radius REAL DEFAULT 1.0;
ALTER TABLE preneural_geometry ADD COLUMN neighbor_ids_json TEXT DEFAULT '[]';
ALTER TABLE preneural_geometry ADD COLUMN source_patch_ids_json TEXT DEFAULT '[]';

-- V8-T1: SignalWindow V8 signal fields
ALTER TABLE preneural_signal_window ADD COLUMN V_mean REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN V_slope REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN release_proxy REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN afferent_current REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN spike_rate REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN spike_regularity REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN timing_precision REAL DEFAULT 0.0;
ALTER TABLE preneural_signal_window ADD COLUMN adaptation_state REAL DEFAULT 0.0;

-- V8-T1: PointSetSlice provenance and stage
ALTER TABLE preneural_pointset_slice ADD COLUMN provenance_hash TEXT DEFAULT '';
ALTER TABLE preneural_pointset_slice ADD COLUMN stage_k INTEGER DEFAULT 0;

-- V8-T2: Transport validation metrics
ALTER TABLE transport_operator ADD COLUMN survival_ratio REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN branching_ratio REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN merge_ratio REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN cycle_consistency REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN boundary_crossing_penalty REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN transport_distortion REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN source_patch_retention REAL DEFAULT 0.0;
ALTER TABLE transport_operator ADD COLUMN signal_drift_after_transport REAL DEFAULT 0.0;

-- V8-T3: Solver diagnostics table
CREATE TABLE IF NOT EXISTS solver_diagnostics (
    diag_id TEXT PRIMARY KEY,
    stage_k INTEGER NOT NULL,
    window_id TEXT NOT NULL,
    diagnostics_json TEXT NOT NULL
);

-- V8-T4: FamilyRecursiveSurfaceIndex maturity/suspension fields
ALTER TABLE family_recursive_surface_index ADD COLUMN maturity_flag TEXT DEFAULT 'candidate';
ALTER TABLE family_recursive_surface_index ADD COLUMN suspension_status TEXT DEFAULT 'ACTIVE';
ALTER TABLE family_recursive_surface_index ADD COLUMN aggregation_role TEXT DEFAULT 'index_root';
ALTER TABLE family_recursive_surface_index ADD COLUMN origin_anchor_id TEXT DEFAULT NULL;
ALTER TABLE family_recursive_surface_index ADD COLUMN t_seed_id TEXT DEFAULT NULL;
