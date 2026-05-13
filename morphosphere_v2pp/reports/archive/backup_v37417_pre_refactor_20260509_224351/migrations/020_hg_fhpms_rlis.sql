-- Migration 020: HG-FHPMS and RLIS Master Schema Package (v37.4.5)
-- Purpose: Introduce the Hebbian-Guided Fiber-Hypergraph Potential Memory Store (HG-FHPMS)
-- and Relativistic Ledger Information Store (RLIS) as defined in the master blueprint.

-- ==============================================================================
-- SECTION 1: HG-FHPMS Tables (Hebbian-Guided Fiber-Hypergraph Potential Memory Store)
-- ==============================================================================

-- 1.1 Spacetime Process Block
CREATE TABLE IF NOT EXISTS fhpms_spacetime_process_block (
    block_id TEXT PRIMARY KEY,
    process_window_id TEXT NOT NULL,
    time_start REAL NOT NULL,
    time_end REAL NOT NULL,
    support_domain_ref TEXT,
    kernel_ref TEXT,
    bandwidth_ref TEXT,
    external_envelope_ref TEXT,
    ledger_ref TEXT,
    origin_anchor_id TEXT,
    coordinate_audit_ref TEXT,
    projection_granularity TEXT,
    projection_confidence REAL,
    bottom_ref TEXT,
    created_at TEXT NOT NULL
);

-- 1.2 PRX Fiber State
-- Represents P/R/Xin as trace measures rather than fixed labels
CREATE TABLE IF NOT EXISTS fhpms_prx_fiber_state (
    fiber_state_id TEXT PRIMARY KEY,
    block_id TEXT NOT NULL,
    p_measure REAL NOT NULL DEFAULT 0.0,
    r_measure REAL NOT NULL DEFAULT 0.0,
    x_measure REAL NOT NULL DEFAULT 0.0,
    u_measure REAL NOT NULL DEFAULT 0.0, -- unresolved/heat-bath
    created_at TEXT NOT NULL,
    FOREIGN KEY(block_id) REFERENCES fhpms_spacetime_process_block(block_id)
);

-- 1.3 Distance-Spacetime Potential
-- Converts distance metrics into motion potentials
CREATE TABLE IF NOT EXISTS fhpms_distance_spacetime_potential (
    potential_id TEXT PRIMARY KEY,
    block_id TEXT NOT NULL,
    phi_d REAL NOT NULL DEFAULT 0.0, -- distance-spacetime measure potential
    phi_p REAL NOT NULL DEFAULT 0.0, -- P anchor absorption/stability potential
    phi_r REAL NOT NULL DEFAULT 0.0, -- R counter-band counter-pressure potential
    phi_x REAL NOT NULL DEFAULT 0.0, -- Xin residual walk potential
    phi_l REAL NOT NULL DEFAULT 0.0, -- ledger sync potential
    phi_m REAL NOT NULL DEFAULT 0.0, -- masking/shield potential
    phi_h REAL NOT NULL DEFAULT 0.0, -- hyperedge binding potential
    created_at TEXT NOT NULL,
    FOREIGN KEY(block_id) REFERENCES fhpms_spacetime_process_block(block_id)
);

-- 1.4 Fiber Connection Transport
CREATE TABLE IF NOT EXISTS fhpms_fiber_connection_transport (
    transport_id TEXT PRIMARY KEY,
    from_block_id TEXT NOT NULL,
    to_block_id TEXT NOT NULL,
    transport_matrix_ref TEXT,
    transport_cost REAL NOT NULL,
    residual_after_transport REAL NOT NULL,
    p_absorbed REAL DEFAULT 0.0,
    r_resolved REAL DEFAULT 0.0,
    xin_generated REAL DEFAULT 0.0,
    unresolved_generated REAL DEFAULT 0.0,
    ledger_sync_strength REAL DEFAULT 0.0,
    created_at TEXT NOT NULL
);

-- 1.5 Hyperedge Binding
CREATE TABLE IF NOT EXISTS fhpms_hyperedge_fiber_binding (
    hyperedge_id TEXT PRIMARY KEY,
    block_refs_json TEXT NOT NULL,
    p_anchor_refs_json TEXT,
    r_band_refs_json TEXT,
    xin_carrier_refs_json TEXT,
    ledger_refs_json TEXT,
    masking_refs_json TEXT,
    attention_refs_json TEXT,
    envelope_refs_json TEXT,
    origin_anchor_refs_json TEXT,
    binding_strength REAL NOT NULL,
    arity INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- 1.6 Origin Anchor Trace
CREATE TABLE IF NOT EXISTS fhpms_origin_anchor_trace (
    origin_anchor_id TEXT PRIMARY KEY,
    raw_event_refs_json TEXT,
    coordinate_audit_refs_json TEXT,
    external_envelope_refs_json TEXT,
    ledger_refs_json TEXT,
    bottom_input_refs_json TEXT,
    t_seed_refs_json TEXT,
    reprojection_status TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- 1.7 Reprojection Trace
CREATE TABLE IF NOT EXISTS fhpms_reprojection_trace (
    trace_id TEXT PRIMARY KEY,
    block_id TEXT NOT NULL,
    origin_anchor_id TEXT NOT NULL,
    t_start REAL,
    t_end REAL,
    x_proxy REAL,
    y_proxy REAL,
    z_proxy REAL,
    coordinate_frame TEXT,
    bottom_ref TEXT,
    projection_confidence REAL,
    granularity_level TEXT,
    loss_reason TEXT,
    created_at TEXT NOT NULL
);

-- 1.8 Hebbian Association Weight
CREATE TABLE IF NOT EXISTS fhpms_hebbian_association_weight (
    weight_id TEXT PRIMARY KEY,
    from_entity_id TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    association_type TEXT NOT NULL,
    weight_value REAL NOT NULL,
    hebbian_gate_status TEXT, -- gated conditions like high Gamma sync
    created_at TEXT NOT NULL
);

-- ==============================================================================
-- SECTION 2: RLIS Tables (Relativistic Ledger Information Store)
-- ==============================================================================

-- 2.1 Ledger Event Spacetime
CREATE TABLE IF NOT EXISTS rlis_ledger_event_spacetime (
    ledger_event_id TEXT PRIMARY KEY,
    ledger_time REAL NOT NULL,
    x_proj REAL,
    y_proj REAL,
    z_proj REAL,
    async_phase REAL,
    proper_time_interval REAL,
    external_envelope_ref TEXT,
    created_at TEXT NOT NULL
);

-- 2.2 Minkowski-like Audit Interval
CREATE TABLE IF NOT EXISTS rlis_minkowski_audit_interval (
    audit_interval_id TEXT PRIMARY KEY,
    event_1_id TEXT NOT NULL,
    event_2_id TEXT NOT NULL,
    interval_squared REAL NOT NULL, -- s_L^2
    information_speed_limit REAL, -- c_I
    causal_status TEXT NOT NULL, -- timelike, spacelike, lightlike
    created_at TEXT NOT NULL
);

-- 2.3 Gamma Sync Binding
CREATE TABLE IF NOT EXISTS rlis_gamma_sync_binding (
    sync_id TEXT PRIMARY KEY,
    ledger_event_id TEXT NOT NULL,
    process_window_id TEXT NOT NULL,
    gamma_strength REAL NOT NULL, -- sync intensity
    sync_verdict TEXT NOT NULL, -- strict_hit, forbidden
    created_at TEXT NOT NULL
);

-- 2.4 Free Energy Variation & DeltaF Split
CREATE TABLE IF NOT EXISTS rlis_free_energy_variation (
    variation_id TEXT PRIMARY KEY,
    ledger_event_id TEXT NOT NULL,
    internal_energy_proxy REAL,
    entropy_proxy REAL,
    free_energy_total REAL NOT NULL,
    delta_f REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rlis_delta_f_split (
    split_id TEXT PRIMARY KEY,
    variation_id TEXT NOT NULL,
    delta_f_p REAL NOT NULL DEFAULT 0.0,
    delta_f_r REAL NOT NULL DEFAULT 0.0,
    delta_f_x REAL NOT NULL DEFAULT 0.0,
    delta_f_m REAL NOT NULL DEFAULT 0.0,
    delta_f_u REAL NOT NULL DEFAULT 0.0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(variation_id) REFERENCES rlis_free_energy_variation(variation_id)
);

-- 2.5 Audit Light Cone
CREATE TABLE IF NOT EXISTS rlis_audit_light_cone (
    cone_id TEXT PRIMARY KEY,
    apex_event_id TEXT NOT NULL,
    forward_cone_refs_json TEXT,
    backward_cone_refs_json TEXT,
    spacelike_exterior_refs_json TEXT,
    created_at TEXT NOT NULL
);
