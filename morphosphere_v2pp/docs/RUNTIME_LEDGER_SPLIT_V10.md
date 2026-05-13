# Runtime/Ledger Split and External Physical Simulator Adapter v1.0

## Purpose

v1.0 answers the architecture critique that SQLite must not be the future high-frequency
physics engine. It keeps SQLite as a ledger and moves runtime records into an external
runtime store. In this minimal implementation the store is JSONL/JSON for local deployment;
the adapter contract explicitly prepares for Zarr/HDF5/PDE/FEM/event-stream backends.

## New invariant

```text
runtime simulation state != SQLite ledger state
```

SQLite records:

- manifests
- source-fact digests
- runtime store indexes
- P/R-Xi governance summaries
- external adapter contracts
- promotion policies
- acceptance reports

Runtime store records:

- cell-state tensor sidecar
- raw-event tensor sidecar
- clock index
- P/R/Xi fast lookup summary

## Promotion loop decision

v1.0 rejects hot-swap. External lab profiles cannot replace runner constants at startup.
They must become staged candidates, pass real-data trial and full replay, then be promoted
only as a new frozen calibration profile.

## Status

This is still diagnostic and append-only:

```text
scientific_run = false
hot_swap_allowed = false
candidate_auto_apply_allowed = false
sqlite_role = ledger_only
real_external_data_gate = BLOCKED_PENDING_REAL_EXTERNAL_DATA
```
