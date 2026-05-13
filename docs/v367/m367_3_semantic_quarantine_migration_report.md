# Morphosphere v36.7.3 Semantic Quarantine Migration Report

## Summary

| Metric | Value |
|---|---:|
| DB integrity | ok |
| Quarantine sidecar rows | 36 |
| Migration audit rows | 36 |
| Semantic-free view manifests | 22 |
| Allowed readout/test text rows | 203 |
| Destructive legacy mutation | 0 |
| Acceptance failed | 0 |

## What changed

v36.7.3 does not delete or rewrite legacy tables. It creates a migration sidecar and semantic-free view manifest. The old DBs remain historical evidence; v36.7.3 defines how new mainline views should hide explanatory/semantic text fields from core computation paths.

## Regression

| Regression | Status |
|---|---|
| v365_backwrite_blocker | PASS |
| pass12_semantic_attack | PASS |
| pass13_semantic_attack | PASS |


## Boundary

This is a quarantine/migration overlay, not a destructive migration. It does not claim that every legacy VARCHAR was removed. It claims that v36.7.3 has a sidecar plan, semantic-free view manifest, and regression checks proving semantic writeback remains blocked.
