# Zarr/HDF5 Field Runtime Adapter v1.2

v1.2 materializes the v1.1 planned chunked field store as a lightweight Zarr v2 sidecar.

## Active runtime payload

- `runtime_store/v12/field_store_v12.zarr`
- Shape: `[10, 8, 8, 1, 5]`
- Channels: `['pressure_proxy', 'shear_proxy', 'diffusion_proxy', 'phase', 'field_energy_proxy']`
- Chunk count: `10`

## HDF5 status

HDF5 is contract-only in this package:

- `runtime_store/v12/hdf5_field_store_contract_v12.json`

## Governance

- SQLite remains ledger-only.
- Source facts are not rewritten.
- Hot-swap remains forbidden.
- P/R remains before Xi.
- This is not `scientific_run`.
- This is not a final PDE/FEM physical solver.

## Acceptance

Stored acceptance: `12 / 12 PASS`.
SQLite quick check: `ok`.
