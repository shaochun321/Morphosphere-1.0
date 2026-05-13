# Morphosphere v36.6 Build Pass5 Report

Pass5 formalizes quick/full deployment modes and adds a module collaboration index.

## Semantics
- Stage 2 bypass is intentional/acceptable when T/O/P/R/Xin + storage + ledger substrate is present.
- Materialization confidence is not truth, importance, or scientific validity.
- Direct FK is never faked.

## Core counts
- process windows: 1633
- process window members: 22128
- preneural process windows: 500
- direct hypernode FK after normalization: 390
- information points: 4575
- external ledger events: 4489

## Materialization confidence
- high_materialization_confidence: 120
- low_materialization_confidence: 842
- medium_materialization_confidence: 671

## Route status
- hybrid_route: 330
- intentional_bypass_to_toprxin: 532
- overlay_governance_route: 271
- stage1_preneural_interface_direct: 500

## Acceptance
- m365 materialized DB integrity: PASS (ok)
- m366 process-window pass3 DB integrity: PASS (ok)
- process_window count present: PASS (1633)
- stage2 bypass treated as legitimate route: PASS (532)
- preneural supplement present: PASS (500)
- hypernode direct FK partial upgrade kept honest: PASS (390)
- full materialized mode retained: PASS (retained)
