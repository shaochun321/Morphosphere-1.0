# Morphosphere v36.6 Pass21 — Ledger Binding Repair + RMI Scale Benchmark

## 0. Position

Pass21 continues the v37-readiness hardening line. It does not implement online native runtime. It repairs the remaining Pass20 ledger-binding gaps as an overlay and expands the RMI benchmark from 855 writer facts into a mixed process-window / trajectory / hyperedge space.

## 1. Ledger binding repair

| Metric | Value |
|---|---:|
| Writer facts audited | 855 |
| Silent NULL ledger refs after repair | 0 |
| Repaired from `pr_xin_to_external_ledger` | 7 |
| Operational FK validation PASS | 855 / 855 |
| Strict external entropy event hits | 848 / 855 |

The 7 Pass20 partial rows all pointed to the same single-frame trajectory `tw25_01-12_000_f047_047`. They now resolve to `win_4` through `pr_xin_to_external_ledger` / process-window external ledger refs. This is an explicit materialized ledger link repair, not a fabricated external entropy event row.

## 2. RMI mixed benchmark

Mixed candidate space size: **5765**.

| Variant | Avg bucket | Max bucket | Collision groups | False-neighbor groups | Verdict |
|---|---:|---:|---:|---:|---|
| H1 | 1.0000 | 532 | 70 | 64 | RISKY |
| H2 | 1.0000 | 14 | 655 | 0 | ACCEPT_WITH_GUARD |
| H3 | 1.0000 | 14 | 655 | 0 | ACCEPT_WITH_GUARD |


Interpretation:

- H1 intentionally uses a coarse measure/category-only key and remains risky.
- H2 adds trajectory/window anchoring and removes false-neighbor groups in this mixed benchmark.
- H3 adds dark-grid and information/process anchoring and remains the preferred v37-readiness key.

## 3. Coordinate invariance CI

Rigid translation CI remains the default gate:

```text
role_changed = 0
max_relative_path_delta = 6.155e-15
status = PASS
```

## 4. Acceptance

- PASS — no_silent_null_ledger_refs: ledger refs populated 855/855
- PASS — seven_ledger_gaps_repaired: repaired_from_pr_xin=7
- PASS — operational_fk_validation_complete: operational_pass=855/855, warnings=0
- PASS — h3_no_false_neighbors_in_mixed_space: H3_false_neighbor_groups=0
- PASS — h1_risk_detected: H1_false_neighbor_groups=64
- PASS — coordinate_invariance_ci_default: role_changed=0; max_relative_path_delta=6.155e-15
- PASS — legacy_db_not_mutated: all repairs written as Pass21 overlay


## 5. Remaining debt

1. The repair closes operational ledger refs but does not create new historical external entropy events.
2. H3 is preferred in the current mixed benchmark, but larger-scale query performance still needs real runtime benchmarking.
3. Online native runtime is still not claimed.
4. Legacy DBs remain immutable; Pass21 is an overlay.
