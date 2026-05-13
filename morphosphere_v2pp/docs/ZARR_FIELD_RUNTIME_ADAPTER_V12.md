# Zarr/HDF5 Field Runtime Adapter v1.2

This layer converts v1.1 external simulator payloads into a chunked field runtime sidecar.

## Runtime payload

`runtime_store/v12/field_store_v12.zarr`

The package uses a dependency-free Zarr v2 directory layout with raw little-endian float64 chunks.

## Ledger payload

SQLite stores manifests, summaries, chunk indexes, replay checks, acceptance records and source fact digests.

## HDF5 boundary

HDF5 is contract-only in this package. A later version can materialize HDF5 through `h5py` or an external writer.

## Boundary

No source fact rewrite. No hot-swap. P/R remains before Xi. Not scientific_run.
