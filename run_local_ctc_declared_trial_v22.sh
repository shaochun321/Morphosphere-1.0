#!/usr/bin/env bash
set -euo pipefail
DB="outputs/morphosphere_ctc_declared_trial_v22_output_database.db"
if [ ! -f "$DB" ]; then
  cp outputs/morphosphere_full_core_v18_output_database.db "$DB"
fi
python3 -S morphosphere_v2pp/scripts/run_ctc_download_extraction_v21.py \
  --db "$DB" \
  --external-csv morphosphere_v2pp/data/ctc_centroid_sample_v21.csv \
  --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_ctc_declared_trial_v22.py \
  --db "$DB" \
  --centroid-csv morphosphere_v2pp/data/ctc_centroid_sample_v21.csv \
  --report-dir morphosphere_v2pp/reports \
  --package-root .
python3 -S morphosphere_v2pp/scripts/run_ctc_declared_trial_acceptance_v22.py "$DB"
