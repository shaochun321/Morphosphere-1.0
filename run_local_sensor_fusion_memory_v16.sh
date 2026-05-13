#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_sensor_fusion_memory_v16_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_sensor_fusion_memory_v16.py --db "$DB" --runtime-dir runtime_store/v16 --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_sensor_fusion_memory_acceptance_v16.py "$DB"
