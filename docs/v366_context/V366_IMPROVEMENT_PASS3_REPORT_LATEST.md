# Morphosphere v36.6 Improvement Pass3 Report

Created: 2026-05-06T04:31:09.635346+00:00

## Purpose

Pass3 corrects the interpretation of Stage 2 routing and renames the former strong/weak window concept into **process window materialization confidence**.

Stage 2 bypass is now treated as an intentional and legitimate current route when the window is supported by the T/O/P/R/Xin + storage + ledger substrate. This avoids treating the early object-surface Stage 2 as a mandatory pass-through layer before the neural-like system is mature.

## Main changes

1. Promoted preneural/interface supplements into the main process window registry.
2. Added `stage2_bypass_and_route_legitimacy_pass3`.
3. Added `process_window_materialization_confidence_pass3`.
4. Added `hypernode_fk_direct_coverage_pass3`.
5. Added Pass3 acceptance and object-count tables.

## Counts

| Item | Count |
|---|---:|
| process_window_registry_pass3_total | 1633 |
| preneural_interface_process_windows | 500 |
| process_window_members_total | 22128 |
| route_legitimacy_rows | 1633 |
| materialization_confidence_rows | 1633 |
| high_materialization_confidence | 120 |
| medium_materialization_confidence | 671 |
| low_materialization_confidence | 842 |
| hypernode_direct_fk_after_normalization | 390 |

## Materialization confidence

{
  "high_materialization_confidence": 120,
  "low_materialization_confidence": 842,
  "medium_materialization_confidence": 671
}

## Stage2 route status

{
  "hybrid_route": 330,
  "intentional_bypass_to_toprxin": 532,
  "overlay_governance_route": 271,
  "stage1_preneural_interface_direct": 500
}

## Combined operational class

{
  "architecturally_valid_needs_more_materialization": 1113,
  "operationally_ready_materialized_route": 520
}

## Interpretation

`materialization_confidence` measures how complete the data linkage is: source anchor, measure binding, ledger binding, backprojection, operator trace, and member density.

`architecture_route_legitimacy` measures whether the route is legitimate under the current architecture. A process window may legitimately bypass old Stage 2 object surfaces if it is carried by T/O/P/R/Xin, storage, and ledger.

Therefore, a Stage 2 bypass no longer automatically downgrades a window. Low materialization confidence now means missing hard evidence links or inferred/proxy-only connections, not architectural failure.

## Boundaries

- source_facts_rewritten = 0
- semantic_writeback_allowed = 0
- Stage2 direct pass-through is not required in the current architecture.
- Hypernode FK remains direct only where normalized target rows exist.

## Integrity

- m366_process_window_pass3.db: ok
- m366_improvement_pass3.db: ok
