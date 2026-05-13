# Morphosphere v36.6 Pass9 — Full-Chain Run Operationalization

## Purpose

Pass9 continues construction with the Pass8 boundary rules. The target is **full-chain full-data materialized operation**: make the implemented chain deployable, inspectable, and operationally clear without treating tests or advisory writer plans as core architecture.

Pass9 does not claim online-life runtime. It does not mutate legacy DBs or source facts.

## What changed

Pass9 adds:

- a full-chain execution plan;
- module input/output contracts;
- external module sync index;
- quick/full run mode contract;
- data completeness matrix;
- run output manifest;
- acceptance checks.

## Full-chain execution status

| Layer | Count / status |
|---|---:|
| information point backprojection | 4575 |
| trajectory links | 13941 |
| T/O/P/R/Xin traces | 532 |
| counter-evidence chains | 532 |
| masking records | 52 |
| external entropy ledger events | 4489 |
| attention rows | 120 |
| hyperedges | 120 |
| hyperedge incidence rows | 855 |
| variational paths | 120 |
| Xin/readout rows | 31 |
| process windows | 1633 |
| process window members | 22128 |
| external definitions | 6 |
| external readouts | 31 |
| readout backwrite blocks | 4 |

## External module placement

External Xin definition and external semantic readout are external modules. They sync offline against carriers/ledger/envelope references and may emit definition refs, readouts, risk flags, hypotheses, or reentry suggestions.

They cannot write source facts, P/R/Xin truth, or semantic labels into the mainline.

The external entropy ledger is not treated as a semantic external module. It remains a core governance ledger.

## Run modes

| Mode | Purpose | Package target |
|---|---|---|
| quick | fast deployment, boundary review, query demo | `Morphosphere_v36_6_quick_deploy_pass9.tar.zst` |
| full_materialized | full-chain full-data materialized operation and audit | `Morphosphere_v36_6_full_materialized_deploy_pass9.tar.zst` |

## Current important gaps

- Hyperedge/hypernode bottom backprojection remains partly proxy/inferred.
- Stage 2 old object-surface route is optional; bypass is legitimate when T/O/P/R/Xin + storage + ledger route is present.
- Query/health scripts are for operability; they are not blueprint core.
- Native writer/direct FK plans are advisory and future-facing.

## Acceptance

- DB integrity: `ok`
- Source facts rewritten: `0`
- Semantic writeback allowed: `0`
- Quick/full modes retained: yes
