# Morphosphere v36.7.5 Consolidated Release Candidate Report

Generated: 2026-05-07T04:31:03.839022+00:00

## Release Status

`RELEASE_CANDIDATE_WITH_KNOWN_WARNINGS`

## Component Rollup

| Component | Key rows | Status | Boundary |
|---|---:|---|---|
| Native anchor baseline | 855 | PASS | Legacy direct FK remains historic 0; new native anchor facts cover 855/855. |
| Safe stress guard config | 27 | PASS | Runtime-config overlay, not realtime fuse. |
| Semantic quarantine | 36 | PASS | Sidecar/view overlay, no destructive mutation. |
| RMI default index | 11530 | PASS | H2/H3 default; H1 audit only. |

## Release Gates

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| native anchor facts | 855 | 855 | PASS |
| native anchor validation | 855 | 855 | PASS |
| strict external entropy hits | 848 | 855 | WARN |
| guard rules | 27 | 27 | PASS |
| guard regression | 0 | 27 | PASS |
| quarantine rows | 36 | >=36 | PASS |
| semantic regression | 3 | 3 | PASS |
| RMI default rows | 11530 | 11530 | PASS |
| RMI H2/H3 false-neighbor groups | H2=0; H3=0 | 0 | PASS |
| coordinate invariance CI | PASS | PASS | PASS |

## Known Warnings

1. Strict historical external entropy event hits remain 848/855, while operational ledger refs cover 855/855.
2. Legacy `direct_fk_available` remains 0 by design; v36.7 native anchor facts are non-destructive overlay baseline.

## Boundary Statement

v36.7.5 is a consolidated hardening release candidate. It is not Online Native Runtime and does not claim 100ms coordinate audit, vector DB runtime, or async complex recursion.
