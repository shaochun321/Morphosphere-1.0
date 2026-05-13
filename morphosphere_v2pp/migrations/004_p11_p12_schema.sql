-- Migration: 004_p11_p12_schema.sql
-- Description: Schema for morphosphere V6 P11 and P12 objects (Archive & Replay)

CREATE TABLE IF NOT EXISTS replay_alignment_record (
    alignment_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    v6_surface_id TEXT NOT NULL,
    legacy_record_id TEXT NOT NULL,
    alignment_score REAL DEFAULT 0.0,
    divergence_reason TEXT DEFAULT ''
);
