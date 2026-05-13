#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_runtime_ledger_v10_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_runtime_ledger_split_v10.py \
  --db "$DB" \
  --runtime-dir runtime_store/v10 \
  --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_runtime_ledger_split_acceptance_v10.py "$DB"
