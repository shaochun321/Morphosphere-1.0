#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_realdata_review_v09_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_realdata_review_v09.py --db "$DB" --report-dir morphosphere_v2pp/reports --data-dir morphosphere_v2pp/data
python3 -S morphosphere_v2pp/scripts/run_realdata_review_acceptance_v09.py "$DB"
