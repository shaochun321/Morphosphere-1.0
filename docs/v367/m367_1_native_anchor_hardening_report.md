# Morphosphere v36.7.1 Native Anchor Hardening Report

## Summary

| Metric | Value |
|---|---:|
| native anchor facts | 855 |
| validation required hits | 855 / 855 |
| operational ledger refs | 855 / 855 |
| strict external entropy hits | 848 / 855 |
| dark-grid zones | 120 |
| legacy rows audited | 855 |
| legacy direct_fk rows | 0 |
| coordinate invariance CI | PASS |
| DB integrity | ok |

## What changed

v36.7.1 creates a new native anchor baseline:

```text
v367_native_anchor_fact
v367_process_window_fk_binding
v367_hypernode_native_backprojection
```

Every row carries materialized refs to information point, trajectory window, evidence bundle, coordinate transform, P/R/Xi measures, ledger ref, dark-grid zone, and anchor hashes.

## Historical honesty

The legacy table remains historically honest:

```text
v366_hypernode_spacetime_backprojection.direct_fk_available = 0 rows direct out of 855
```

v36.7.1 does not mutate that table. It builds new native anchor facts on top of Pass20/Pass21 writer-emitted facts.

## Ledger boundary

Operational ledger refs are complete. Strict historical external entropy event hits remain 848/855; the remaining 7 are materialized repair links, not newly invented source events.
