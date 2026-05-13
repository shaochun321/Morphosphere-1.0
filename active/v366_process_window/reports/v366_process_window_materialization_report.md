# Morphosphere v36.6 Process Window Materialization Report
Generated: `2026-05-06T03:08:16Z`
## Purpose
This artifact builds the v36.6 `process_window` and `hypernode_spacetime_backprojection` materialization layer on top of the v36.5 full-chain materialized data. It is not a validation-only report and does not rewrite any source/base database.
## Core conclusion
`process_window` can be materialized now as an additive v36.6 index. `hypernode_spacetime_backprojection` can also be generated, but most v35H hypernode-to-spacetime links remain **proxy/inferred**, not hard direct foreign keys. The DB explicitly marks this boundary.
## Object counts

| Metric | Value |
|---|---:|
| `attention_process_windows` | 120 |
| `band_coupler_process_windows` | 210 |
| `coordinate_nonlocal_audit_examples` | 50 |
| `coordinate_nonlocal_relation_count` | 1682 |
| `direct_hypernode_fk_count` | 0 |
| `hyperedge_process_windows` | 120 |
| `hyperedge_relation_count` | 2625 |
| `hypernode_backprojection_count` | 855 |
| `ledger_binding_count` | 791 |
| `measure_binding_count` | 893 |
| `process_window_count` | 1133 |
| `process_window_member_count` | 20128 |
| `proxy_hypernode_backprojection_count` | 855 |
| `trajectory_process_windows` | 532 |
| `variational_process_windows` | 120 |
| `xin_carrier_process_windows` | 31 |
| `pragma_integrity_check` | ok |

## Process window counts by kind

| Kind | Count |
|---|---:|
| `attention_path_integral` | 120 |
| `evidence_trajectory_pr_xin` | 532 |
| `hyperedge_incidence_process` | 120 |
| `r_spacetime_band_coupler` | 210 |
| `variational_action_path` | 120 |
| `xin_carrier_external_readout` | 31 |

## Acceptance report

| Check | Status | Observed | Note |
|---|---|---:|---|
| process windows materialized | **PASS** | `1133` | v36.6 process_window registry generated |
| trajectory evidence windows included | **PASS** | `532` | 底层 evidence / P-R-Xin windows present |
| hyperedge process windows included | **PASS** | `120` | v35H hyperedges represented as process windows |
| hypernode backprojection generated | **PASS** | `855` | Every incidence row should get an audit backprojection row |
| coordinate nonlocal proxy examples retained | **PASS** | `50` | Coordinate-far/process-linked examples available; proxy evidence only |
| semantic null guard held | **PASS** | `1` | No semantic labels introduced into process_window mainline |
| raw coordinate audit retained | **PASS** | `1` | Coordinates are hidden from mainline interpretation but retained for audit |
| source facts not rewritten | **PASS** | `0` | Output DB is additive materialized index only |
| direct/proxy FK separated | **PASS** | `direct=0, proxy=855` | v35H overlay lacks hard FK to base evidence; marked proxy |
| integrity check | **PASS** | `ok` | Filled after final commit |

## Top coordinate-nonlocal proxy examples

These are not physical nonlocality claims. They mean: the same hyperedge/process binds nodes whose inferred/proxy cell-sphere backprojections are coordinate-far.

| Hyperedge | Node A | Node B | Distance proxy | Relation class | Evidence status |
|---|---|---|---:|---|---|
| `he35h_0012` | `hn35h_0170` | `hn35h_0187` | 11.2743 | `coordinate_nonlocal_process_linked` | `PROXY_EVIDENCE_NOT_DIRECT_FK` |
| `he35h_0067` | `hn35h_0487` | `hn35h_0555` | 10.9860 | `coordinate_nonlocal_process_linked` | `PROXY_EVIDENCE_NOT_DIRECT_FK` |
| `he35h_0055` | `hn35h_0454` | `hn35h_0488` | 10.9640 | `coordinate_nonlocal_process_linked` | `PROXY_EVIDENCE_NOT_DIRECT_FK` |
| `he35h_0085` | `hn35h_0613` | `hn35h_0647` | 10.9588 | `coordinate_nonlocal_process_linked` | `PROXY_EVIDENCE_NOT_DIRECT_FK` |
| `he35h_0107` | `hn35h_0020` | `hn35h_0037` | 10.9210 | `coordinate_nonlocal_process_linked` | `PROXY_EVIDENCE_NOT_DIRECT_FK` |

## Architecture placement
`process_window` is the v36.6 mainline working unit. It binds information, time, support, process/operator trace, external envelope and ledger reference. It does not delete coordinates; it hides coordinate interpretation from the mainline while requiring raw coordinate audit.

`hypernode_spacetime_backprojection` is the audit bridge between v35H hypernodes/hyperedges and the lower evidence chain: information point, trajectory window, spacetime cell, coordinate transform, and P/R/Xi measure.

## Important boundary
The output separates `direct_fk_available` from inferred/proxy backprojection. At this stage v35H overlays do not contain full hard foreign keys into v25-v34 evidence tables, so the backprojection rows are intentionally marked as proxy/inferred. This prevents the new v36.6 layer from pretending that all upper-layer relations are already grounded by direct source FKs.
