# Morphosphere v36.6 Pass17 — Hardening and Source-Rerun Calibration

## Purpose
Pass17 addresses hardening after Pass15/16: backprojection directness, semantic text quarantine, localized stress calibration, and CTC02 upper overlay projection.

## Outputs

| DB | Purpose |
|---|---|
| `m366_pass17_backprojection_hardening.db` | directness tiering, dark-grid anchor, measure hash collision audit, FK upgrade plan |
| `m366_pass17_semantic_payload_audit.db` | text field inventory and quarantine plan |
| `m366_pass17_source_rerun_calibration.db` | localized source rerun calibration matrix |
| `m366_pass17_ctc02_upper_overlay.db` | CTC01/02 upper overlay projection comparison |
| `m366_pass17_hardening_summary.db` | rollup summary |

## Key results

### Backprojection hardening
- Backprojection rows audited: **855**
- Raw native direct FK rows: **0**
- Safe L2 candidates: **855**
- Dark-grid zone anchors: **855**
- Composite anchor hashes generated: **855**

Raw direct FK remains 0. L1/L2 anchors are useful but are not native direct facts.

### Semantic payload quarantine
- Text-like columns inventoried: **633**
- Quarantine/review columns: **36**
- Readout/report/test text is allowed outside core computation path.

### Localized stress calibration
- Calibration cases: **60**
- Calibration rows: **1620**
- Safe pressure rows: **588**
- P-core collapse rows: **252**

### CTC02 upper overlay
- Projection rows: **532**
- Sequence 01 rows: **241**
- Sequence 02 rows: **291**

## Remaining debt
1. Upstream writers must emit native direct references for L3 direct FK.
2. Legacy DBs were not mutated; semantic quarantine is inventory/plan, not destructive migration.
3. CTC02 overlay is projected, not a full upper rerun.
4. Source-level calibration is still over materialized v25 data, not online runtime.
