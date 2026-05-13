# Morphosphere v36.6 Pass8 — Blueprint-Aligned Full-Chain Run Boundary Cleanup

## Purpose

Pass8 corrects the project boundary after Pass7. It keeps the engineering improvements that help full-chain full-data operation, but separates them from the uploaded v36.6 blueprint core.

The construction target for this phase is **offline full-chain full-data materialized operation**, not online-life runtime and not merely validation.

## Main decision

The project is now split into five explicit classes:

1. **Blueprint core** — objects directly required by the uploaded v36.6 blueprint.
2. **Full-chain materialized data** — implemented outputs required to run and inspect the full chain.
3. **External modules** — read-only readout/definition modules; outputs may be readout/proposal/risk flags, not mainline truth.
4. **Test / operability surface** — query scripts, health scoring, sample backtraces, deployment checks.
5. **Advisory engineering suggestions** — writer upgrade plans, directness debt, native-write candidates.

## Key counts

| Metric | Count |
|---|---:|
| process windows | 1633 |
| process window members | 22128 |
| information point 3D/4D backprojections | 4575 |
| trajectory links | 13941 |
| T/O/P/R/Xin traces | 532 |
| counter-evidence chains | 532 |
| masking records | 52 |
| ledger events | 4489 |
| attention rows | 120 |
| hyperedges | 120 |
| hyperedge incidence rows | 855 |
| variational paths | 120 |
| Xin/readout rows | 31 |
| external modules | 4 |
| external readout rows | 31 |
| readout backwrite blocks | 4 |

## External module positioning

External modules are **not** the mainline storage system and are **not** allowed to write semantic labels, P/R truth, source facts, or raw coordinates. They are read-only side modules that can produce external definitions, readout results, classifications, risk flags, hypotheses, or reentry suggestions.

The external entropy ledger is classified separately as a **core governance ledger**, not as a semantic external module. It audits energy-like ledger quantities, dissipation, noise, anomalies, and proxy boundaries, but does not write source facts.

## Stage 2 route correction

Old Stage 2 object surface is optional at this phase. The current neural-substrate route may legitimately be:

```text
T/O/P/R/Xin + storage system + external entropy ledger + external readout boundary
```

Therefore Stage 2 bypass is not treated as failure when downstream T/O/P/R/Xin and ledger/process-window route is present.

## Test / operability surfaces

Query scripts, module health scoring, collaboration edges, deployment checks, and backtrace samples are kept because they improve usability for full-chain full-data operation. They are explicitly marked as operability surfaces, not blueprint core objects.

## Advisory demarcation

Pass7 writer-upgrade tables are retained as advisory only. They may improve future native writing, but they are not required by the uploaded v36.6 blueprint and must not be treated as raw direct FK evidence.

## Acceptance

- DB integrity: `ok`
- Source facts rewritten: `0`
- Semantic writeback allowed: `0`
- Legacy DBs mutated: `0`
- Full-chain materialized run preserved: yes


## Pass3 confidence counts carried forward

| Class | Count |
|---|---:|
| high materialization confidence | 120 |
| medium materialization confidence | 671 |
| low materialization confidence | 842 |
| legitimate Stage2 bypass current architecture | 532 |
