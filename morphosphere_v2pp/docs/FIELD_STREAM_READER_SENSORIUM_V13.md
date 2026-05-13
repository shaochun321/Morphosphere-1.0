# Field Stream Reader + Online Sensorium Adapter v1.3

## Purpose

v1.3 connects the chunked field runtime introduced in v1.2 to the online sensorium path. It reads the Zarr-style field chunks directly, derives non-semantic streaming events, bridges them into trajectory hints, and records P/R/Xi response summaries in SQLite as a ledger only.

## Main boundary

SQLite remains a ledger, not a runtime engine. Field payloads stay in `runtime_store/v12/field_store_v12.zarr`. v1.3 reads those chunks and writes only summaries, chunk-reader manifests, P/R response proxies, replay outcomes, and acceptance reports.

## New flow

```text
field_store_v12.zarr chunks
  -> field_stream_event_v13
  -> field_stream_to_sensorium_bridge_v13
  -> streaming_pr_response_v13
  -> field_stream_replay_result_v13
```

## What this version does not claim

- Not a scientific run.
- Not a final PDE/FEM solver.
- Not a real HDF5 runtime.
- Not a semantic recognition layer.
- Not a hot-swap promotion loop.

## Protected rules

- Do not rewrite source facts.
- Do not let external profiles hot-swap mainline weights.
- Keep P/R before Xi.
- Keep Xi as unresolved residue after P/R, not a replacement for P/R.
