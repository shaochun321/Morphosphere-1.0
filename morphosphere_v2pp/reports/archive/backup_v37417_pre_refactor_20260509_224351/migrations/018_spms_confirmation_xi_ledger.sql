-- ═══════════════════════════════════════════════════════════
-- Migration: 018_spms_confirmation_xi_ledger.sql
-- V8.5: Consolidates SPMS Confirmation Graph and Xi Residue ledgers
-- Replaces old schemas from 008/009/010

DROP TABLE IF EXISTS occupancy_measure;
DROP TABLE IF EXISTS pr_graph_transition_record;
DROP TABLE IF EXISTS masking_counterevidence_record;
DROP TABLE IF EXISTS xi_residue_record;
DROP TABLE IF EXISTS object_hypothesis;
DROP TABLE IF EXISTS spacetime_cell;
DROP TABLE IF EXISTS information_fiber;
DROP TABLE IF EXISTS spacetime_fiber_binding;
DROP TABLE IF EXISTS transport_current_edge;

-- ═══════════════════════════════════════════════════════════
-- Migration 018: SPMS Core + Confirmation Graph + Xi Lifecycle
--                + Ledger Temporal Binding + Perturbation Tables
-- V8.3 §5, V8.5 §4/§7/§8, V36.8
-- ═══════════════════════════════════════════════════════════

-- ─── SPMS Core (V8.3 §5.2-5.6) ─────────────────────────

CREATE TABLE IF NOT EXISTS spacetime_cell (
    cell_uid         TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    stage_k          INTEGER NOT NULL,
    window_id        TEXT NOT NULL,
    node_id          INTEGER NOT NULL,
    clock_start      INTEGER DEFAULT 0,
    clock_end        INTEGER DEFAULT 1,
    x                REAL DEFAULT 0.0,
    y                REAL DEFAULT 0.0,
    z                REAL DEFAULT 0.0,
    normal_x         REAL DEFAULT 0.0,
    normal_y         REAL DEFAULT 0.0,
    normal_z         REAL DEFAULT 1.0,
    boundary_distance REAL DEFAULT 0.0,
    support_radius   REAL DEFAULT 1.0,
    source_patch_ids_json  TEXT DEFAULT '[]',
    topology_neighbors_json TEXT DEFAULT '[]',
    coordinate_frame_id TEXT DEFAULT 'preneural_local',
    provenance_hash  TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sc_run_stage ON spacetime_cell(run_id, stage_k);
CREATE INDEX IF NOT EXISTS idx_sc_window ON spacetime_cell(window_id);

CREATE TABLE IF NOT EXISTS information_fiber (
    fiber_id         TEXT PRIMARY KEY,
    cell_uid         TEXT NOT NULL REFERENCES spacetime_cell(cell_uid),
    V_mean           REAL DEFAULT 0.0,
    V_slope          REAL DEFAULT 0.0,
    release_proxy    REAL DEFAULT 0.0,
    afferent_current REAL DEFAULT 0.0,
    spike_rate       REAL DEFAULT 0.0,
    spike_regularity REAL DEFAULT 0.0,
    timing_precision REAL DEFAULT 0.0,
    adaptation_state REAL DEFAULT 0.0,
    signal_uncertainty REAL DEFAULT 0.0,
    compression_loss REAL DEFAULT 0.0,
    source_signal_refs_json TEXT DEFAULT '{}',
    calibration_profile TEXT DEFAULT 'diagnostic',
    provenance_hash  TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_if_cell ON information_fiber(cell_uid);

CREATE TABLE IF NOT EXISTS spacetime_fiber_binding (
    binding_id       TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    clock_n          INTEGER DEFAULT 0,
    window_id        TEXT NOT NULL,
    spacetime_cell_id TEXT NOT NULL REFERENCES spacetime_cell(cell_uid),
    information_fiber_id TEXT NOT NULL REFERENCES information_fiber(fiber_id),
    source_cell_ids_json TEXT DEFAULT '[]',
    source_patch_ids_json TEXT DEFAULT '[]',
    binding_type     TEXT DEFAULT 'direct' CHECK(binding_type IN ('direct','aggregated','proxy','inferred')),
    proxy_provenance_id TEXT,
    calibration_profile TEXT DEFAULT 'diagnostic',
    provenance_hash  TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_sfb_cell ON spacetime_fiber_binding(spacetime_cell_id);
CREATE INDEX IF NOT EXISTS idx_sfb_fiber ON spacetime_fiber_binding(information_fiber_id);

CREATE TABLE IF NOT EXISTS transport_current_edge (
    edge_id          TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    from_cell_uid    TEXT NOT NULL REFERENCES spacetime_cell(cell_uid),
    to_cell_uid      TEXT NOT NULL REFERENCES spacetime_cell(cell_uid),
    transport_weight REAL DEFAULT 0.0,
    current_mass     REAL DEFAULT 0.0,
    geometry_cost    REAL DEFAULT 0.0,
    normal_cost      REAL DEFAULT 0.0,
    boundary_cost    REAL DEFAULT 0.0,
    signal_cost      REAL DEFAULT 0.0,
    source_patch_overlap REAL DEFAULT 0.0,
    fragility_penalty REAL DEFAULT 0.0,
    accepted         INTEGER DEFAULT 1,
    transport_variant TEXT DEFAULT 'mainline',
    cycle_consistency_local REAL DEFAULT 0.0,
    boundary_crossing_penalty REAL DEFAULT 0.0,
    signal_drift     REAL DEFAULT 0.0,
    gating_failure_reason TEXT DEFAULT '',
    provenance_hash  TEXT DEFAULT '',
    total_cost       REAL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_tce_run ON transport_current_edge(run_id);
CREATE INDEX IF NOT EXISTS idx_tce_from ON transport_current_edge(from_cell_uid);
CREATE INDEX IF NOT EXISTS idx_tce_to ON transport_current_edge(to_cell_uid);

-- ─── Object Hypothesis (V8.3 §5.5, V8.5 §4) ─────────

CREATE TABLE IF NOT EXISTS object_hypothesis (
    hypothesis_id    TEXT PRIMARY KEY,
    hypothesis_type  TEXT NOT NULL CHECK(hypothesis_type IN
        ('P_candidate','R_candidate','origin_candidate','boundary_candidate',
         'proto_structure','xi_proto','refuted_candidate')),
    stage_k          INTEGER NOT NULL,
    run_id           TEXT NOT NULL,
    status           TEXT DEFAULT 'candidate' CHECK(status IN
        ('O_candidate','PR_candidate','mask_supported','recursion_eligible',
         'compute_committed','science_certified','refuted','suspended',
         'xi_carried','emergence_alerted','candidate')),
    member_cell_uids_json TEXT DEFAULT '[]',
    spatial_support_json  TEXT DEFAULT '[]',
    temporal_support_json TEXT DEFAULT '[]',
    support_score    REAL DEFAULT 0.0,
    source_decomposition_ref TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_oh_run ON object_hypothesis(run_id);
CREATE INDEX IF NOT EXISTS idx_oh_status ON object_hypothesis(status);

-- ─── Occupancy Measure (V8.3 §5.6) ───────────────────

CREATE TABLE IF NOT EXISTS occupancy_measure (
    measure_id       TEXT PRIMARY KEY,
    hypothesis_id    TEXT NOT NULL REFERENCES object_hypothesis(hypothesis_id),
    cell_uid         TEXT NOT NULL REFERENCES spacetime_cell(cell_uid),
    membership_mass  REAL DEFAULT 0.0,
    membership_entropy REAL DEFAULT 0.0,
    occupancy_rank   INTEGER DEFAULT 0,
    transport_support REAL DEFAULT 0.0,
    signal_support   REAL DEFAULT 0.0,
    geometry_support REAL DEFAULT 0.0,
    masking_support  REAL DEFAULT 0.0,
    replay_support   REAL DEFAULT 0.0,
    boundary_support REAL DEFAULT 0.0,
    counterevidence_mass REAL DEFAULT 0.0,
    artifact_penalty REAL DEFAULT 0.0,
    core_margin_label TEXT DEFAULT 'unknown' CHECK(core_margin_label IN ('core','margin','unknown'))
);
CREATE INDEX IF NOT EXISTS idx_om_hyp ON occupancy_measure(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_om_cell ON occupancy_measure(cell_uid);

-- ─── P/R Confirmation Graph Transition (V8.5 §4.3) ─

CREATE TABLE IF NOT EXISTS pr_graph_transition_record (
    transition_id    TEXT PRIMARY KEY,
    hypothesis_id    TEXT NOT NULL REFERENCES object_hypothesis(hypothesis_id),
    from_state       TEXT NOT NULL,
    to_state         TEXT NOT NULL,
    run_id           TEXT NOT NULL,
    conditions_met_json TEXT DEFAULT '{}',
    evidence_refs_json TEXT DEFAULT '[]',
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_pgtr_hyp ON pr_graph_transition_record(hypothesis_id);

-- ─── Masking Counterevidence (V8.5 §5) ────────────

CREATE TABLE IF NOT EXISTS masking_counterevidence_record (
    record_id        TEXT PRIMARY KEY,
    hypothesis_id    TEXT NOT NULL,
    masking_type     TEXT NOT NULL,
    baseline_score   REAL DEFAULT 0.0,
    perturbed_score  REAL DEFAULT 0.0,
    verdict          TEXT DEFAULT 'inconclusive',
    details          TEXT DEFAULT '',
    run_id           TEXT NOT NULL,
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_mcr_hyp ON masking_counterevidence_record(hypothesis_id);

-- ─── Xi Residue (V8.3 §8, V8.5 §7) ────────────────

CREATE TABLE IF NOT EXISTS xi_residue_record (
    xi_id            TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    source_hypothesis_id TEXT,
    xi_type          TEXT DEFAULT 'unknown' CHECK(xi_type IN
        ('stochastic_noise','unresolved_memory','proto_structure',
         'boundary_uncertain','numerical_residue','unknown')),
    xi_state         TEXT DEFAULT 'held' CHECK(xi_state IN
        ('held','decaying','proto_candidate','promoted',
         'quarantined','discarded_after_audit')),
    mass_current     REAL DEFAULT 1.0,
    mass_previous    REAL DEFAULT 1.0,
    decay_rate       REAL DEFAULT 0.15,
    persistence_window_count INTEGER DEFAULT 0,
    relation_support_score REAL DEFAULT 0.0,
    occupancy_support_score REAL DEFAULT 0.0,
    carryover_allowed INTEGER DEFAULT 1,
    audit_reason     TEXT DEFAULT '',
    created_at       TEXT DEFAULT '',
    updated_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_xi_run ON xi_residue_record(run_id);
CREATE INDEX IF NOT EXISTS idx_xi_state ON xi_residue_record(xi_state);

-- Backward-compatible column additions for DBs with old xi_residue_record (migration 009).
-- These are no-ops on fresh DBs where 018 created the table above.
-- SQLite does not support IF NOT EXISTS for ALTER TABLE, so we catch errors at app level.

-- ─── Free Energy Routing (V36.8 fix) ─────────────

CREATE TABLE IF NOT EXISTS v368_free_energy_routing (
    routing_id       TEXT PRIMARY KEY,
    run_id           TEXT NOT NULL,
    window_id        TEXT NOT NULL,
    delta_f_ext      REAL DEFAULT 0.0,
    gamma_sync       REAL DEFAULT 1.0,
    pi_P             REAL DEFAULT 0.2,
    pi_R             REAL DEFAULT 0.2,
    pi_X             REAL DEFAULT 0.2,
    pi_M             REAL DEFAULT 0.2,
    pi_U             REAL DEFAULT 0.2,
    alloc_P          REAL DEFAULT 0.0,
    alloc_R          REAL DEFAULT 0.0,
    alloc_X          REAL DEFAULT 0.0,
    alloc_M          REAL DEFAULT 0.0,
    alloc_U          REAL DEFAULT 0.0,
    created_at       TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_fer_run ON v368_free_energy_routing(run_id);
