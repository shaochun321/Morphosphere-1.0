-- Migration: 011_mainline_manifest_crosswalk.sql
-- Mainline convergence P4: clarify manifest counts and add V8.5-to-mainline crosswalk.
-- This is additive and does not create v8.6/v9 or scientific-run semantics.

ALTER TABLE run_manifest ADD COLUMN physical_cell_count INTEGER DEFAULT 0;
ALTER TABLE run_manifest ADD COLUMN spacetime_cell_count INTEGER DEFAULT 0;
ALTER TABLE run_manifest ADD COLUMN extra_json TEXT DEFAULT '{}';

CREATE TABLE IF NOT EXISTS v85_to_mainline_crosswalk (
    diagnostic_table TEXT PRIMARY KEY,
    prior_mainline_concept TEXT NOT NULL,
    semantic_role TEXT NOT NULL,
    source_of_truth TEXT NOT NULL,
    allowed_use TEXT NOT NULL,
    forbidden_use TEXT NOT NULL,
    intentionally_empty_when TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR REPLACE INTO v85_to_mainline_crosswalk
(diagnostic_table, prior_mainline_concept, semantic_role, source_of_truth, allowed_use, forbidden_use, intentionally_empty_when)
VALUES
('run_manifest','run identity and calibration contract','source','contracts.RunManifest plus run_manifest table','Fix diagnostic run identity, schema/rules version, execution mode, and count semantics.','Do not infer scientific validity or biology readiness from run identity alone.',''),
('spacetime_cell','preneural_geometry / pointset view','derived','derived from PreNeuralCarrierSlice / PreNeuralPointSetSlice','Runtime diagnostic coordinate record for a cell-like carrier at one window/stage.','Do not treat as a physical cell source-of-truth or replace PhysicalCellGraphState.',''),
('information_fiber','preneural_signal_window view','derived','derived from SignalWindow / diagnostic dynamic driver','Runtime diagnostic signal-window record attached to a spacetime carrier.','Do not treat as raw electrophysiology or final biological spike evidence.',''),
('spacetime_fiber_binding','carrier-to-signal co-generation binding','derived','derived from spacetime_cell and information_fiber rows','Audit inseparability of spacetime carrier and signal fiber in diagnostic runs.','Do not interpret binding as proof of object formation.',''),
('transport_current_edge','transport process view, not necessarily transport_operator','derived','derived from preneural transport builder and SPMS populator','Diagnostic transport-current evidence between carrier rows.','Do not claim true transport realism while weights/gating/costs remain proxy or trivial.',''),
('object_hypothesis','P/R candidate view, not final p_band/r_band','derived','derived from PR decomposition and SPMS hypothesis population','Diagnostic candidate object/hypothesis row from decomposition and occupancy support.','Do not treat as certified object, frozen P band, or scientific conclusion.',''),
('o_candidate_record','O candidate surface','proxy_or_derived','stage2 object surface / diagnostic runner','Track O lineage candidate records and formation mode where available.','Do not claim O formation when formation_mode is pass_through_proxy.',''),
('t_surface','legacy/mainline T surface','derived_or_intentionally_empty','stage2 object surface when populated','Use when populated with slice and transport references; otherwise consult crosswalk.','Do not fail a SPMS-only diagnostic run solely because legacy T rows are intentionally empty.','SPMS-layer diagnostic run does not materialize legacy T surface rows.'),
('p_band_record','legacy/mainline primary band','derived_or_intentionally_empty','stage2 freezer when populated','Use only when populated by mainline freezer with origin anchors.','Do not replace object_hypothesis or treat empty rows as failed SPMS diagnostic formation.','Diagnostic run reports P/R candidates through object_hypothesis instead of frozen bands.'),
('r_band_record','legacy/mainline residual band','derived_or_intentionally_empty','stage2 freezer when populated','Use only when populated by mainline freezer with residual anchors.','Do not infer no residual pressure solely from empty legacy R band rows.','Diagnostic run reports residual pressure through Xi/residue tables instead of frozen bands.'),
('xi_residue_record','residual evidence / Xi residue pool','derived','Xi residue evaluator / decomposition residual','Audit unresolved residual pressure and support domains in diagnostic runs.','Do not treat Xi rows as final refutation or final object discovery.',''),
('relation_entropy_record','relation entropy diagnostic ledger','report_only','Xi/relation entropy evaluator','Inspect diagnostic relation entropy and its support distribution/provenance.','Do not use for refutation support while entropy remains synthetic or stage-index derived.',''),
('proxy_provenance','proxy/synthetic component audit ledger','report_only','runtime provenance writer','Declare which diagnostic components are proxy, synthetic, or pilot and when to replace them.','Do not hide proxy usage or reinterpret proxy outputs as final biology.',''),
('emergence_alert','diagnostic emergence alert','report_only','emergence alert evaluator','Synthetic or diagnostic alerting for pipeline behavior and hard-case routing.','Do not write synthetic emergence alerts to production/scientific statistics.','');
