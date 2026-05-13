# External Physical Simulator Adapter v1.1

This append-only layer stores external physical simulator payloads in `runtime_store/v11` sidecars while keeping SQLite as a ledger.

- field rows: 640
- cell state rows: 500
- emitted event rows: 1500
- mapping rows: 1500
- replay scenarios: 10
- acceptance: 34 / 34 PASS

Boundary: diagnostic proxy only; not scientific_run, not final PDE/FEM physics, no hot-swap, no source fact rewrite.
