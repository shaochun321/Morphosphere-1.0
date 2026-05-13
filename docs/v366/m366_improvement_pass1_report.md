# Morphosphere v36.6 Improvement Pass 1
This is an additive improvement pass over the v36.6 process-window materialization. It does not modify prior DBs.
## Output
- DB: `m366_improvement_pass1.db`
- Integrity check: `ok`
## Generated Tables
- `stage2_object_surface_materialization_audit`: 532
- `preneural_interface_operator_trace`: 500
- `counter_masking_coverage_audit`: 532
- `hypernode_direct_fk_upgrade_candidate`: 855
- `process_window_quality_score`: 1133

## Stage 2 Object Surface Audit
- Trajectory rows audited: 532
- Rows with O candidate ref: 532
- Direct FK to `o_candidate_record`: 0
- Direct FK to `o_candidate_surface`: 0
- Base Stage-2 material exists: `18` o-candidate records, `18` object surfaces, `50` online O-candidate ticks.
Conclusion: Stage 2 is not absent, but the current v25-derived materialized chain does not direct-FK its `o25_*` O candidates into the older Stage-2 object-surface tables. This is a bypass/weak-materialization risk, not a proof that Stage 2 never existed.

## Preneural / Interface Bundle Trace
- resolved_stage1_to_preneural_operator_trace: 500
Conclusion: The shared Stage-1/Stage-2 preneural interface is present as `spacetime_fiber_binding -> information_fiber -> preneural_node_state`, with preneural edges/synaptic edges available. It needs to become a first-class `operator_trace_ref` in process windows.

## Counter-evidence / Masking Coverage
- category_level_masking_coverage: 532
Conclusion: R-chain coverage is broad; masking is mostly category-level in the v25 materialized chain. Concrete mask IDs should be added per R-chain/window.

## Hypernode Direct-FK Upgrade Plan
- blocked_requires_source_ref_normalization: 223
- bottom_candidate_needs_source_ref_normalization: 243
- ledger_candidate_needs_window_fk: 112
- mask_candidate_needs_source_ref_normalization: 113
- overlay_to_overlay_direct_candidate: 35
- requires_stage2_macro_object_surface_materialization: 129
Conclusion: Current backprojection remains proxy/inferred. This pass identifies where overlay-to-overlay IDs can be normalized and where bottom FK requires source_ref redesign.

## Process Window Quality
- strong_materialized_window: 640
- usable_materialized_window: 43
- weak_materialized_window: 450
Conclusion: process_window is usable as a main index. Next pass should upgrade weak windows by adding direct measure/ledger/backprojection bindings and explicit preneural operator traces.

## Acceptance
- imp_001 `stage2_audit_built`: **PASS**; observed `532`; requirement `532 trajectory rows audited`
- imp_002 `preneural_trace_built`: **PASS**; observed `500`; requirement `>= 500 interface traces from spacetime_fiber_binding`
- imp_003 `counter_masking_coverage_built`: **PASS**; observed `532`; requirement `532 counter-evidence chains audited`
- imp_004 `hypernode_fk_upgrade_plan_built`: **PASS**; observed `855`; requirement `855 hypernodes analyzed`
- imp_005 `process_window_quality_scored`: **PASS**; observed `1133`; requirement `1133 process windows scored`
- imp_006 `source_facts_not_rewritten`: **PASS**; observed `0 writes to source DBs`; requirement `old DBs must remain untouched`
- imp_007 `direct_vs_inferred_separated`: **PASS**; observed `direct FK not fabricated`; requirement `proxy/inferred must remain marked`
