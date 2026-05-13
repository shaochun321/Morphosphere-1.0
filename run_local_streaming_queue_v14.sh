#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_streaming_queue_v14_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_streaming_queue_v14.py --db "$DB" --runtime-dir runtime_store/v14 --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_streaming_queue_acceptance_v14.py "$DB"
