#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
DB="outputs/morphosphere_zarr_field_v12_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_zarr_field_adapter_v12.py --db "$DB" --runtime-dir runtime_store/v12 --source-runtime-dir runtime_store/v11 --report-dir morphosphere_v2pp/reports --package-root .
python3 -S morphosphere_v2pp/scripts/run_zarr_field_acceptance_v12.py "$DB"
