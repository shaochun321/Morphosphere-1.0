#!/usr/bin/env bash
set -euo pipefail
python3 -S morphosphere_v2pp/scripts/run_multirate_sync_v15.py --db outputs/morphosphere_multirate_sync_v15_output_database.db --runtime-dir runtime_store/v15 --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_multirate_sync_acceptance_v15.py outputs/morphosphere_multirate_sync_v15_output_database.db
