# Morphosphere v36.7.5 Consolidated Release Candidate Blueprint

## Version Position

`v36.7.5_consolidated_release_candidate`

## Purpose

Consolidate v36.7.1-v36.7.4 hardening outputs into a single release candidate without mutating legacy source facts or historical DBs.

## Included Baselines

1. v36.7.1 Native Anchor Hardening: 855/855 native anchor facts over materialized targets.
2. v36.7.2 Safe Stress Guard Config: 27 guard rule cells loaded and regressed.
3. v36.7.3 Semantic Quarantine Migration: 36 quarantine sidecar rows, semantic-free view manifest.
4. v36.7.4 RMI Default Index + Regression: H2/H3 default indexes, H1 audit-only.

## Release Candidate Rules

- Legacy DBs are not destructively migrated.
- Legacy `direct_fk_available = 0` remains historically honest.
- v36.7 native anchor facts provide the new non-destructive baseline.
- H2/H3 are default RMI indexes; H1 is forbidden for production routing.
- Safe stress guard is a runtime-config table, not an online fuse.
- Semantic text is quarantined into sidecars/views, not mainline truth.
- Online Native Runtime is not claimed.
