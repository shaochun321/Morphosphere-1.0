#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_ctc_source_verified_v24_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_ctc_source_verified_acceptance_v24.py "$DB"
echo "v2.4 source-verified CTC package acceptance passed."
