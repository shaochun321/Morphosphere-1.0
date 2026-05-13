# Morphosphere v37.0 Native Runtime Prototype

## Position
This build starts the next stage after v36.8 Mainline Consolidated Final. It is a **small offline native-runtime prototype**, not an online native runtime.

```text
source_event -> information_point_write -> process_window_write -> native_anchor_write -> T/O/P/R/Xin -> ledger -> guard -> RMI lookup -> attention -> hyperedge/variational -> external readout
```

No legacy DB is mutated. Source facts are not rewritten. External readout remains read-only.

## Core counts
| Metric | Value |
|---|---:|
| samples | 80 |
| stages per sample | 12 |
| stage trace rows | 960 |
| RMI hits | 80 |
| RMI false-neighbor flags | 0 |
| semantic write sum | 0 |
| acceptance FAIL | 0 |
| acceptance WARN | 0 |
| DB integrity | ok |

## Role distribution
| Role family | Count |
|---|---:|
| MIXED | 22 |
| P | 25 |
| R | 8 |
| XIN | 25 |

## Acceptance
| Check | Status | Metric | Required |
|---|---|---:|---|
| single_run_id | PASS | 1 | 1 |
| sample_count_50_to_100 | PASS | 80 | 50..100 |
| all_samples_have_full_stage_trace | PASS | 960 | 960 |
| source_facts_not_rewritten | PASS | 0 | 0 |
| process_window_native_write | PASS | 80 | 80 |
| native_anchor_native_write | PASS | 80 | 80 |
| toprxin_native_write | PASS | 80 | 80 |
| ledger_binding_native_write | PASS | 80 | 80 |
| guard_action_written | PASS | 80 | 80 |
| rmi_lookup_participated | PASS | 80 | >=76 |
| semantic_write_allowed_zero | PASS | 0 | 0 |
| legacy_db_mutated_zero | PASS | 0 | 0 |

## What this proves
1. A single `run_id` can emit source, information point, process window, native anchor, T/O/P/R/Xin, ledger, guard, RMI, attention, hyperedge/variational, and readout rows.
2. Process windows and anchors are emitted inside the prototype run rather than merely described as post-hoc objects.
3. External readout is still read-only: `semantic_write_allowed = 0`.
4. RMI participates as a lookup stage without replacing coordinate audit or dark-grid anchoring.

## What this does not prove
1. It is not an online native runtime.
2. It does not re-run the physical source or regenerate v25 from raw image data.
3. It does not implement 100ms coordinate audit, vector database runtime, PDE fields, or async complex recursion.
4. It does not mutate legacy DBs or convert historical `direct_fk_available=0` rows into raw direct facts.
