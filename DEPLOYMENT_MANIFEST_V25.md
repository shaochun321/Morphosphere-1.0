# Morphosphere v2.5 Deployment Manifest

SQLite quick_check: `ok`

## Counts

| table | rows |
|---|---:|
| `information_point_v25` | 4575 |
| `coordinate_transform_trace_v25` | 4575 |
| `trajectory_window_trace_v25` | 532 |
| `calculation_recipe_v25` | 7 |
| `p_spacetime_measure_v25` | 532 |
| `r_counter_measure_v25` | 532 |
| `xi_residual_surface_v25` | 532 |
| `attention_yield_event_v25` | 262 |
| `decision_evidence_bundle_v25` | 532 |
| `evidence_runtime_artifact_manifest_v25` | 7 |

## Packages

- `ms25_core.zip`: code/docs/scripts/configs/schemas/data; excludes DB/runtime/source ZIP.
- `ms25_db_*.zip`: output DBs, including the v2.5 evidence ledger.
- `ms25_runtime.zip`: runtime sidecars, including `runtime_store/v25/*.jsonl`.
- `ms25_src.part00` ...: split CTC source ZIP.

## Reconstruct source ZIP

```bash
cat ms25_src.part* > morphosphere_v25_full_chain/external_data/ctc/Fluo-N2DH-GOWT1.zip
```
