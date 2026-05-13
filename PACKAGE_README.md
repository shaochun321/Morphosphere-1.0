# Morphosphere Full Core v1.8 Package

This is the corrected full deployable core package. It uses the full v1.3 engineering package as the base and overlays the v1.4-v1.8 layer artifacts, scripts, runtime sidecars, reports, and the latest v1.8 ledger database.

## What was fixed

Earlier outputs for v1.4-v1.8 were layer packages, not complete deployable core packages. This package restores the full core tree:

- `morphosphere_v2pp/src/`
- `morphosphere_v2pp/migrations/`
- `morphosphere_v2pp/data_contracts/`
- `morphosphere_v2pp/scripts/`
- `morphosphere_v2pp/docs/`
- `morphosphere_v2pp/reports/`
- `runtime_store/v10` through `runtime_store/v18`
- `outputs/morphosphere_full_core_v18_output_database.db`

## Local check

```bash
./run_local_full_core_v18.sh
```

This performs a deployment sanity check without mutating source facts or applying the candidate calibration profile.

## Current boundary

This package is still diagnostic. It is not `scientific_run`, not final biology, not hot-swap, and not an automatically promoted calibration profile.
