# Morphosphere v8.5.3 Physical-Freeze Quickstart

This package is a diagnostic physical-freeze build. It does not create v8.6/v9 and does not mark any output as `scientific_run`.

## One-command local run

From the package root:

```bash
./run_local_v853_physical.sh
```

The wrapper defaults to `PYTHON_FLAGS=-S` so the diagnostic path can run with only the Python standard library. Override it when needed:

```bash
PYTHON_FLAGS="" ./run_local_v853_physical.sh
```

Primary output database:

```text
outputs/morphosphere_v853_basic_physics_output_database.db
```

## Manual equivalent

```bash
cd morphosphere_v2pp
python -S run_smoke.py
python -S run_v85_diagnostic.py --calibration_profile basic_physics_v1 --execution_mode diagnostic_full --scientific_use_allowed false
python -S scripts/run_acceptance_sql.py v85_full_diagnostic_run.db
python -S run_v853_validation.py --db v85_full_diagnostic_run.db --config configs/v853_validation.json
python -S run_v853_validation.py --db v85_full_diagnostic_run.db --config configs/v853_validation.json
python -S scripts/export_v853_artifact_manifest.py v85_full_diagnostic_run.db
python -S scripts/run_v853_behavioral_acceptance.py v85_full_diagnostic_run.db
python -S scripts/export_db_summary.py v85_full_diagnostic_run.db reports/db_summary.json
```

## Unified CLI examples

```bash
cd morphosphere_v2pp
PYTHONPATH=src python -S -m morphosphere.cli run diagnostic --calibration_profile basic_physics_v1 --db v85_full_diagnostic_run.db
PYTHONPATH=src python -S -m morphosphere.cli validate v852 --db v85_full_diagnostic_run.db
PYTHONPATH=src python -S -m morphosphere.cli run validation --db v85_full_diagnostic_run.db --config configs/v853_validation.json
PYTHONPATH=src python -S -m morphosphere.cli validate v853 --db v85_full_diagnostic_run.db
```

## Current alignment additions

This rebuilt package adds the v8.5.3 alignment exports requested by the方案:

- deterministic `threshold_sweep` perturbation;
- visible `failed_expectation_report` table;
- plan-aligned `transport_cost_matrix_record` export;
- plan-aligned `xi_residue_mass_record` export;
- object-evidence terms with explicit `xi_pressure_penalty`;
- external DB checksum in `BUILD_METADATA.json` and `.sha256` file.

## Scientific-use boundary

All outputs remain diagnostic-only. They must not be interpreted as final biology, a scientific run, production threshold guidance, or a v8.6/v9 claim.
