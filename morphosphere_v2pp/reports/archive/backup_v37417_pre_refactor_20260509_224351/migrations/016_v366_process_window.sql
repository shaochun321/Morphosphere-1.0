-- Migration: 016_v366_process_window.sql
-- v36.6: Semanticless Process Window + Coordinate Hidden Measure Architecture
-- Blueprint ref: Morphosphere_v36_6_semanticless_process_window_coordinate_hidden_blueprint
-- This is additive. No legacy DB mutation. No semantic mainline objects.

-- ═══ P1: Process Window Registry ═══
-- The minimal working window: I(information), T(time), S(space), Π(process), E(envelope), L(ledger)
CREATE TABLE IF NOT EXISTS v366_process_window_registry (
    pw_id              TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    source_adapter_id  TEXT NOT NULL,
    window_k           INTEGER NOT NULL,
    -- I: information payload / measure contribution
    information_payload_hash TEXT NOT NULL DEFAULT '',
    information_cell_count   INTEGER NOT NULL DEFAULT 0,
    information_fiber_count  INTEGER NOT NULL DEFAULT 0,
    -- T: time span / ordering
    time_window_start  INTEGER NOT NULL DEFAULT 0,
    time_window_end    INTEGER NOT NULL DEFAULT 0,
    time_ordering_index INTEGER NOT NULL DEFAULT 0,
    -- S: support domain / kernel / bandwidth
    space_support_domain_json TEXT NOT NULL DEFAULT '{}',
    space_kernel_type   TEXT NOT NULL DEFAULT 'local_neighborhood',
    space_bandwidth     REAL NOT NULL DEFAULT 1.0,
    -- Π: process operators / recursion trace
    process_operator_chain_json TEXT NOT NULL DEFAULT '[]',
    process_recursion_depth     INTEGER NOT NULL DEFAULT 0,
    -- E: external input envelope ref
    envelope_ref       TEXT DEFAULT NULL,
    -- L: external ledger balance ref
    ledger_balance_ref TEXT DEFAULT NULL,
    ledger_free_energy_proxy REAL DEFAULT 0.0,
    -- metadata
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P2: Coordinate Hidden Measure Binding ═══
-- Spacetime measure proxy: coordinates hidden from mainline, retained for audit
CREATE TABLE IF NOT EXISTS v366_coordinate_hidden_measure_binding (
    binding_id         TEXT PRIMARY KEY,
    pw_id              TEXT NOT NULL,
    run_id             TEXT NOT NULL,
    from_cell_uid      TEXT NOT NULL,
    to_cell_uid        TEXT NOT NULL,
    -- Measure proxies (coordinate-free)
    mu_spacetime       REAL NOT NULL DEFAULT 0.0,  -- μ_ST spacetime measure proxy
    mu_information_energy REAL NOT NULL DEFAULT 0.0, -- μ_IE information-energy metric proxy
    -- Audit scaffold (coordinates preserved for evidence chain)
    raw_distance_3d    REAL DEFAULT 0.0,
    raw_coord_from_json TEXT DEFAULT '[]',
    raw_coord_to_json   TEXT DEFAULT '[]',
    -- Process context
    transport_edge_ref TEXT DEFAULT NULL,
    hyperedge_ref      TEXT DEFAULT NULL,
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (pw_id) REFERENCES v366_process_window_registry(pw_id),
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P3: External Envelope Ref ═══
-- Each data source wraps its output in an envelope describing reality constraints
CREATE TABLE IF NOT EXISTS v366_external_envelope_ref (
    envelope_id        TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    source_adapter_id  TEXT NOT NULL,
    envelope_type      TEXT NOT NULL DEFAULT 'continuous_field',
    -- Reality constraints
    spatial_extent_json TEXT NOT NULL DEFAULT '{}',
    temporal_extent_json TEXT NOT NULL DEFAULT '{}',
    noise_budget        REAL DEFAULT 0.0,
    dissipation_budget  REAL DEFAULT 0.0,
    anomaly_budget      REAL DEFAULT 0.0,
    -- Ledger accounting
    energy_in           REAL DEFAULT 0.0,
    energy_out          REAL DEFAULT 0.0,
    ledger_closure_gap  REAL DEFAULT 0.0,
    created_at          TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P4: Semantic Null Guard ═══
-- Contract: mainline must not hold explicit semantic truth
CREATE TABLE IF NOT EXISTS v366_semantic_null_guard (
    guard_id           TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    pw_id              TEXT NOT NULL,
    semantic_write_attempted INTEGER DEFAULT 0,
    semantic_write_blocked   INTEGER DEFAULT 0,
    guard_verdict      TEXT NOT NULL DEFAULT 'CLEAN',
    checked_tables_json TEXT NOT NULL DEFAULT '[]',
    violation_details_json TEXT DEFAULT NULL,
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (pw_id) REFERENCES v366_process_window_registry(pw_id)
);

-- ═══ P5: Process Hyperedge Relation ═══
-- Multi-body relation: connects multiple process windows, P/R/Xi, ledger, envelope
CREATE TABLE IF NOT EXISTS v366_process_hyperedge_relation (
    hyperedge_id       TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    -- Members (sparse COO style)
    member_pw_ids_json TEXT NOT NULL DEFAULT '[]',
    member_hypothesis_ids_json TEXT DEFAULT '[]',
    member_xi_ids_json TEXT DEFAULT '[]',
    member_envelope_ids_json TEXT DEFAULT '[]',
    -- Relation properties
    relation_type      TEXT NOT NULL DEFAULT 'transport_linked',
    incidence_weight   REAL DEFAULT 1.0,
    locality_type      TEXT DEFAULT 'coordinate_nonlocal_but_process_linked',
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);

-- ═══ P6: Xin Carrier Minimal Binding ═══
-- Xin in the coordinate-hidden architecture: residual carrier with minimal mainline footprint
CREATE TABLE IF NOT EXISTS v366_xin_carrier_minimal_binding (
    xin_binding_id     TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    xi_residue_id      TEXT NOT NULL,
    -- Minimal carrier fields (no ontological interpretation)
    source_T_refs_json TEXT DEFAULT '[]',
    process_window_refs_json TEXT DEFAULT '[]',
    support_domain_json TEXT DEFAULT '{}',
    residual_mass_proxy REAL DEFAULT 0.0,
    ledger_ref         TEXT DEFAULT NULL,
    envelope_ref       TEXT DEFAULT NULL,
    reentry_policy     TEXT DEFAULT 'hold_for_audit',
    attention_priority REAL DEFAULT 0.0,
    -- External classification ref (semantic readout only)
    external_definition_ref TEXT DEFAULT NULL,
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id),
    FOREIGN KEY (xi_residue_id) REFERENCES xi_residue_record(residue_id)
);

-- ═══ P7: Source Adapter Envelope ═══
-- Dual-source support: each adapter registers here with its properties
CREATE TABLE IF NOT EXISTS v366_source_adapter_envelope (
    adapter_id         TEXT PRIMARY KEY,
    run_id             TEXT NOT NULL,
    adapter_name       TEXT NOT NULL,
    adapter_type       TEXT NOT NULL,  -- 'cell_sphere_3d' or 'cell_2d_real'
    geometry_model     TEXT NOT NULL,  -- '3d_sphere' or '2d_plane'
    signal_model       TEXT NOT NULL,  -- 'electromechanical' or 'calcium_dynamics'
    cell_count         INTEGER NOT NULL DEFAULT 300,
    coordinate_frame   TEXT NOT NULL DEFAULT 'adapter_local',
    scale_contract_json TEXT NOT NULL DEFAULT '{}',
    window_policy_json  TEXT NOT NULL DEFAULT '{}',
    proxy_provenance_id TEXT DEFAULT NULL,
    created_at         TEXT DEFAULT NULL,
    FOREIGN KEY (run_id) REFERENCES run_manifest(run_id)
);
