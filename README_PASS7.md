# Morphosphere v36.6 Pass7 Build Report

## Purpose

Pass7 converts the Pass6 query surface into a **native-write readiness layer**. It does not claim new biological truth and does not mutate legacy DBs. Its job is to tell future modules exactly what they must write natively so `process_window`, preneural operator trace, hypernode backprojection and external readout no longer rely on post-hoc inference.

## Core Results

| Item | Count / Status |
|---|---:|
| process windows | 1633 |
| process window members | 22128 |
| Pass6 lineage traces | 532 |
| native write contracts | 7 |
| upstream writer upgrade plans | 6 |
| native write candidate examples | 532 |
| hypernode raw direct FK | 0 |
| hypernode normalized direct candidates | 390 |
| Stage2 intentional bypass routes | 532 |

## What changed

Pass7 adds seven queryable surfaces:

```text
pass7_native_write_contract
pass7_upstream_writer_upgrade_plan
pass7_canonical_id_resolver
pass7_directness_debt_index
pass7_native_write_candidate_index
pass7_query_recipe_library
pass7_module_readiness_matrix
```

## Interpretation

- Stage 2 old object surface remains optional. Bypass into T/O/P/R/Xin + storage + ledger + external modules is treated as an intentional architecture route.
- Hypernode backprojection remains conservative: raw direct FK is not overclaimed. Normalized direct candidates are preserved as upgrade candidates only.
- `process_window_id` should become a native writer output for all new modules.
- Preneural interface should emit `operator_trace_ref` and `process_window_id` natively.
- External readout must remain read-only and must not write semantic labels into the mainline.

## Acceptance

All blocking Pass7 checks pass.
