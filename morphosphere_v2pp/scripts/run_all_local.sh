#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python_cmd="${PYTHON:-python3}"
read -r -a python_flags <<< "${PYTHON_FLAGS:--S}"
mkdir -p reports
"$python_cmd" "${python_flags[@]}" run_smoke.py | tee reports/run_all_smoke.log
"$python_cmd" "${python_flags[@]}" run_v85_diagnostic.py --calibration_profile basic_physics_v1 --execution_mode diagnostic_full --scientific_use_allowed false | tee reports/run_all_diagnostic.log
"$python_cmd" "${python_flags[@]}" scripts/run_acceptance_sql.py v85_full_diagnostic_run.db | tee reports/run_all_acceptance.log
"$python_cmd" "${python_flags[@]}" run_v853_validation.py --db v85_full_diagnostic_run.db --config configs/v853_validation.json | tee reports/run_all_v853_validation_1.log
"$python_cmd" "${python_flags[@]}" run_v853_validation.py --db v85_full_diagnostic_run.db --config configs/v853_validation.json | tee reports/run_all_v853_validation_2.log
"$python_cmd" "${python_flags[@]}" scripts/export_v853_artifact_manifest.py v85_full_diagnostic_run.db | tee reports/run_all_artifact_manifest.log
"$python_cmd" "${python_flags[@]}" scripts/run_v853_behavioral_acceptance.py v85_full_diagnostic_run.db | tee reports/run_all_v853_acceptance.log
"$python_cmd" "${python_flags[@]}" scripts/export_db_summary.py v85_full_diagnostic_run.db reports/db_summary.json | tee reports/run_all_db_summary.log
printf '\nMorphosphere v8.5.3 physical-freeze local run complete. See reports/.\n'
