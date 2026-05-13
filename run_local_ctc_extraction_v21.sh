#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_ctc_extraction_v21_output_database.db"
python3 -S morphosphere_v2pp/scripts/run_ctc_download_extraction_v21.py --db "$DB" --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_ctc_download_extraction_acceptance_v21.py "$DB"
