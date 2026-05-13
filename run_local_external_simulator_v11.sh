#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_external_simulator_v11_output_database.db"
if [ ! -f "$DB" ]; then
  cp outputs/morphosphere_runtime_ledger_v10_output_database.db "$DB"
fi
python3 -S morphosphere_v2pp/scripts/run_external_simulator_adapter_v11.py --db "$DB" --runtime-dir runtime_store/v11 --report-dir morphosphere_v2pp/reports --package-root .
python3 -S morphosphere_v2pp/scripts/run_external_simulator_acceptance_v11.py "$DB"
