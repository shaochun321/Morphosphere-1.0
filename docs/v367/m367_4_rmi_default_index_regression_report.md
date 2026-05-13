# Morphosphere v36.7.4 RMI Default Index + Regression Baseline

## Summary
v36.7.4 promotes validated H2/H3 RMI variants into default query indexes and freezes v36.7.1–v36.7.3 regression gates.

## Counts

| Metric | Value |
|---|---:|
| H2 default index rows | 5765 |
| H3 default index rows | 5765 |
| Total default index rows | 11530 |
| Coordinate invariance CI | PASS |
| Native anchor coverage inherited | 855/855 |
| Safe stress guard regression inherited | 27/27 |
| Semantic backwrite regression inherited | 3/3 |

## Boundary
This is an SQLite/default-index overlay. It does not introduce Faiss, vector DB runtime, online runtime, or destructive legacy migration.
