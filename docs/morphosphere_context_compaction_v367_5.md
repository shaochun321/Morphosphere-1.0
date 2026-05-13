# Morphosphere Context Compaction - v36.7.5

## Current Stage

The project has moved from v36.6 materialized integration and Pass15-Pass21 stress/hardening into v36.7 engineering hardening.

## Recent Build Summary

- v36.7.1: Native anchor hardening; 855/855 native anchor facts over materialized targets.
- v36.7.2: Safe stress guard config; 27 rules loaded and regression-matched.
- v36.7.3: Semantic quarantine migration; 36 sidecar rows and semantic-free view manifest.
- v36.7.4: RMI default index and regression; H2/H3 default, H1 audit-only.
- v36.7.5: Consolidated release candidate; unified gates, artifacts, boundaries, and known warnings.

## Key Boundary

Legacy DBs are not rewritten. Historical `direct_fk_available = 0` is preserved. New v36.7 anchor facts provide a non-destructive baseline.

## Known Warning

Strict external entropy event hits remain 848/855. Operational ledger refs cover 855/855, but 7 single-frame cases are not strict historical external entropy event hits.

## Next Suggested Step

v36.7.6 should focus on final RC polishing: strict ledger gap resolution plan, a single status command, release notes, and final package QA. Do not start v37 Online Native Runtime until RC gates are stable.
