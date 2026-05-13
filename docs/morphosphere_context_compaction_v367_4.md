# Morphosphere Context Compaction — v36.7.4

## Current stage
The project is in `v36.7_engineering_hardening`. The goal is to turn Pass15–Pass21 evidence into default engineering baselines, not to add new theory.

## Latest hardening stages

| Stage | Purpose | Status |
|---|---|---|
| v36.7.1 | Native anchor baseline over writer-emitted facts | Complete |
| v36.7.2 | Safe stress envelope runtime-config overlay | Complete |
| v36.7.3 | Semantic quarantine sidecar and semantic-free view manifest | Complete |
| v36.7.4 | RMI H2/H3 default index + regression baseline | Complete |

## Key data facts
- v36.7.1 native anchor facts: 855 rows.
- v36.7.2 safe stress rules: 27 rules; guard regression 27/27.
- v36.7.3 semantic quarantine: 36 sidecar rows; semantic regression 3/3.
- v36.7.4 default RMI index: H2 = 5765, H3 = 5765.
- H1 is disabled for production and retained only as collision warning baseline.
- Coordinate invariance CI remains PASS.

## Boundaries
- No online native runtime claim.
- No true PDE / continuous physical field claim.
- No retroactive legacy raw direct FK claim.
- No semantic readout text in core computation.
- No H1 production index.

## Recommended next stage
`v36.7.5 Consolidated Release Candidate`: merge v36.7.1–v36.7.4 checks into one release gate and add a single status command.
