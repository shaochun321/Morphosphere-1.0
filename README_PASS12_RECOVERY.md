# Morphosphere v36.6 Pass12 Recovery Execution Report

This is a recovery build because the previous Pass12 artifacts were missing from `/mnt/data`.

## Scope

Pass12 is an offline execution layer over materialized data. It does not claim native synchronous runtime.

## Counts

- Trajectory windows covered: 532
- Native-shaped skeleton trace rows: 3724
- Stress projection rows: 3192
- Sample full traces: 20
- Process windows available from Pass3: 1633
- Process-window members available from Pass3: 22128
- DB integrity: ok

## Stress result matrix

| Stress | P→R projected | R/P→Xin projected | Stable retained | Boundary blocked |
|---|---:|---:|---:|---:|
| S1 coordinate jitter | 1 | 0 | 531 | 0 |
| S2 support dropout | 23 | 0 | 509 | 0 |
| S3 counter-evidence boost | 513 | 0 | 19 | 0 |
| S4 Xin residual spike | 1 | 462 | 69 | 0 |
| S5 masking failure | 450 | 67 | 15 | 0 |
| S6 semantic backwrite attack | 0 | 0 | 0 | 532 |


## Interpretation

- S1 coordinate jitter: mostly stable.
- S2 support dropout: limited P→R projection.
- S3 counter-evidence boost: large R activation projection.
- S4 Xin residual spike: large Xin projection.
- S5 masking failure: strong R and some Xin projection.
- S6 semantic backwrite attack: all windows blocked by readout boundary.

## Boundary

These rows are deterministic offline stress projections over materialized T/O/P/R/Xin windows. They do not rewrite source facts, do not generate a native synchronized runtime, and do not upgrade inferred links into direct facts.
