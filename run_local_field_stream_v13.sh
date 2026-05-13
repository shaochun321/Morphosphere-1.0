#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_field_stream_v13_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_field_stream_adapter_v13.py --db "$DB" --runtime-dir runtime_store/v12 --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_field_stream_acceptance_v13.py "$DB"
