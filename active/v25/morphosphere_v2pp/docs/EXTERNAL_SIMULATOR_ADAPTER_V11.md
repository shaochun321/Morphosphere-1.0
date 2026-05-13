# External Physical Simulator Adapter v1.1

This layer introduces an external physical runtime sidecar while keeping SQLite as a ledger only.

## Intent

`v1.1` responds to the runtime bottleneck critique: high-frequency field physics, tensor state and simulator payloads should not be executed inside SQLite. SQLite remains the audit ledger for manifests, digests, replay summaries, P/R/Xi boundaries and acceptance records.

## Runtime payload

The external simulator payload is stored under `runtime_store/v11`:

- `external_simulator_config_v11.json`
- `external_field_tensor_v11.jsonl`
- `external_cell_state_tensor_v11.jsonl`
- `external_emitted_event_tensor_v11.jsonl`
- `external_to_raw_event_mapping_v11.jsonl`
- `zarr_field_store_planned_manifest_v11.json`

## Boundaries

- Not `scientific_run`.
- Not a final PDE/FEM solver.
- No source fact rewrite.
- No hot-swap of mainline parameters.
- P/R remains before Xi.
- External simulator output is evidence payload, not physical truth.

## Next step

`v1.2` should turn the planned Zarr/HDF5 field store into a real chunked array runtime adapter.
