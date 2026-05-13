# Morphosphere v36.7.4 — RMI Default Index + Regression Baseline Blueprint

## Version positioning
`v36.7.4_rmi_default_index_regression_baseline`

This stage does not add theory. It hardens Pass20/Pass21 RMI evidence into a default engineering baseline.

## Scope
1. Promote H2/H3 RMI hash variants to default query indexes.
2. Retain H1 only as risk-control / collision warning baseline.
3. Freeze regression gates: coordinate invariance, native anchor coverage, safe stress guard, semantic quarantine, and RMI false-neighbor checks.
4. Preserve legacy DBs; this is an overlay/default baseline.

## Acceptance gates
- H2/H3 populated.
- H3 false-neighbor groups = 0 on current mixed candidate space.
- H1 disabled for production use.
- Coordinate invariance CI = PASS.
- v36.7.1, v36.7.2, v36.7.3 inherited gates PASS.
