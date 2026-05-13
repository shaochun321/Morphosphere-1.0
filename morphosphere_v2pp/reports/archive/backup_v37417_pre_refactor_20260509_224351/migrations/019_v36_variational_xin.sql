-- ═══════════════════════════════════════════════════════════
-- Migration 019: Variational Xin & Information-Energy Metric
-- V36 §3-4, V36.1 §3-5
-- ═══════════════════════════════════════════════════════════

-- ─── Dissipative Source Registry (V36 §3.3) ─────────

CREATE TABLE IF NOT EXISTS v36_dissipative_source_registry (
    source_id        TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    cell_uid         TEXT NOT NULL,
    source_type      TEXT DEFAULT 'unknown' CHECK(source_type IN
        ('geometric_curvature','signal_gradient','transport_friction',
         'boundary_interaction','numerical_viscosity','unknown')),
    dissipation_rate REAL DEFAULT 0.0,
    is_steady_state  INTEGER DEFAULT 0,
    confidence       REAL DEFAULT 0.0,
    window_id        TEXT DEFAULT '',
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_dsr_run ON v36_dissipative_source_registry(run_id);
CREATE INDEX IF NOT EXISTS idx_dsr_cell ON v36_dissipative_source_registry(cell_uid);

-- ─── Delta Xin Field (V36 §4.1, fallback) ──────────

CREATE TABLE IF NOT EXISTS v36_delta_xin_field (
    field_id         TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    cell_uid         TEXT NOT NULL,
    stage_k          INTEGER DEFAULT 0,
    xin_value        REAL DEFAULT 0.0,
    xin_type         TEXT DEFAULT 'variational' CHECK(xin_type IN
        ('variational','finite_difference','proxy','unresolved')),
    source_term      TEXT DEFAULT '',
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_dxf_run ON v36_delta_xin_field(run_id);

-- ─── Variational State Vector (V36.1 §3) ────────────

CREATE TABLE IF NOT EXISTS v361_variational_state_vector (
    state_id         TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    window_id        TEXT NOT NULL,
    cell_uid         TEXT NOT NULL,
    -- V36.1 §3.1: State components
    phi_info         REAL DEFAULT 0.0,  -- information density
    phi_geo          REAL DEFAULT 0.0,  -- geometric curvature proxy
    phi_transport    REAL DEFAULT 0.0,  -- transport current magnitude
    phi_boundary     REAL DEFAULT 0.0,  -- boundary interaction
    phi_signal       REAL DEFAULT 0.0,  -- signal field strength
    phi_occupancy    REAL DEFAULT 0.0,  -- occupancy measure
    -- Derived
    state_norm       REAL DEFAULT 0.0,
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_vsv_run ON v361_variational_state_vector(run_id);
CREATE INDEX IF NOT EXISTS idx_vsv_cell ON v361_variational_state_vector(cell_uid);

-- ─── Lagrangian Terms (V36.1 §4) ────────────────────

CREATE TABLE IF NOT EXISTS v361_lagrangian_term (
    term_id          TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    window_id        TEXT NOT NULL,
    cell_uid         TEXT NOT NULL,
    term_name        TEXT NOT NULL,
    term_value       REAL DEFAULT 0.0,
    coefficient      REAL DEFAULT 1.0,
    -- V8.5 governance: coefficient is meta-proxy, not physical constant
    is_meta_proxy    INTEGER DEFAULT 1,
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_lt_run ON v361_lagrangian_term(run_id);

-- ─── Euler-Lagrange Residual (V36.1 §4.2) ──────────

CREATE TABLE IF NOT EXISTS v361_euler_lagrange_residual (
    residual_id      TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    window_id        TEXT NOT NULL,
    cell_uid         TEXT NOT NULL,
    el_residual_norm REAL DEFAULT 0.0,
    boundary_term    REAL DEFAULT 0.0,
    constraint_violation REAL DEFAULT 0.0,
    xin_variational  REAL DEFAULT 0.0,  -- the actual variational Xin
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_elr_run ON v361_euler_lagrange_residual(run_id);

-- ─── Information-Energy Metric (V36.1 §5) ───────────

CREATE TABLE IF NOT EXISTS v361_information_energy_metric (
    metric_id        TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    cell_uid_a       TEXT NOT NULL,
    cell_uid_b       TEXT NOT NULL,
    d_IE             REAL DEFAULT 0.0,  -- information-energy distance
    path_length      INTEGER DEFAULT 0,
    path_cost        REAL DEFAULT 0.0,
    -- V36 §4.4 CONSTRAINT: mu_IE != real physics metric
    is_physics_metric INTEGER DEFAULT 0 CHECK(is_physics_metric = 0),
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_iem_run ON v361_information_energy_metric(run_id);

-- ─── Relation Readout Proxy (V36.1 §6) ─────────────

CREATE TABLE IF NOT EXISTS v361_relation_readout_proxy (
    proxy_id         TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    cell_uid_a       TEXT NOT NULL,
    cell_uid_b       TEXT NOT NULL,
    relation_type    TEXT DEFAULT 'unknown' CHECK(relation_type IN
        ('approaching','receding','stationary','oscillating','unknown')),
    d_IE_value       REAL DEFAULT 0.0,
    confidence       REAL DEFAULT 0.0,
    -- V8.5: STRICTLY READ-ONLY, no semantic label writeback
    can_write_semantic_label INTEGER DEFAULT 0 CHECK(can_write_semantic_label = 0),
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_rrp_run ON v361_relation_readout_proxy(run_id);
