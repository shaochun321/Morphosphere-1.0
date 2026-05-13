# Morphosphere v8.5.3 Validation & Perturbation Release Notes

Release role: diagnostic validation build on top of v8.5.2.

This release does not create v8.6/v9, does not enable `scientific_run`, and does not make final biology claims. It adds perturbation and behavioral acceptance scaffolding to test whether the v8.5.2 diagnostic mechanisms respond in expected directions.

## Main additions

- `morphosphere_v2pp/run_v853_validation.py`
- `morphosphere_v2pp/src/morphosphere/cli.py`
- `morphosphere_v2pp/src/morphosphere/validation/v853.py`
- `morphosphere_v2pp/src/morphosphere/active_exec/perturbations/definitions.py`
- `morphosphere_v2pp/scripts/run_v853_behavioral_acceptance.py`
- `morphosphere_v2pp/scripts/verify_v853_release.py`
- `morphosphere_v2pp/configs/v853_validation.json`
- `morphosphere_v2pp/migrations/013_v853_validation_perturbation.sql`
- `morphosphere_v2pp/QUICKSTART_V853.md`

## Entrypoints

```bash
cd morphosphere_v2pp
python run_smoke.py
python run_v85_diagnostic.py
python scripts/run_acceptance_sql.py v85_full_diagnostic_run.db
python run_v853_validation.py
python scripts/run_v853_behavioral_acceptance.py v85_full_diagnostic_run.db
```

Optional CLI:

```bash
PYTHONPATH=src python -m morphosphere.cli run diagnostic
PYTHONPATH=src python -m morphosphere.cli run validation
PYTHONPATH=src python -m morphosphere.cli validate v852
PYTHONPATH=src python -m morphosphere.cli validate v853
```

## Behavioral perturbations

- `signal_shuffle`: relation normalized entropy should increase.
- `geometry_shift`: mean geometry cost should increase.
- `boundary_flip`: rejected transport fraction should increase.
- `masking_injection`: mean O support score should decrease.
- `xi_pressure_injection`: Xi quarantine pressure should increase.

## Validation status

- v8.5.2 acceptance SQL: 21/21 PASS
- v8.5.3 behavioral acceptance SQL: 14/14 PASS
- SQLite integrity_check: ok
- execution_mode: diagnostic_full
- scientific_run: false

## v8.5.3 Hardening addendum

This addendum keeps the release inside v8.5.3. It does not create v8.6/v9 and does not enable scientific_run.

Hardening additions:

- Reproducibility fingerprinting for validation metrics and perturbation effect signatures.
- Repeat-run comparison in `v853_reproducibility_report`.
- Artifact fingerprint manifest in `v853_release_artifact_manifest`.
- Additive migration `014_v853_hardening_reproducibility.sql`.
- Behavioral acceptance now checks reproducibility and artifact-manifest presence.

The recommended final verification command is:

```bash
cd morphosphere_v2pp
python scripts/verify_v853_release.py
```

## Rebuild alignment addendum

This improved package keeps the v8.5.3 diagnostic boundary and adds the following hardening items:

- deterministic `threshold_sweep` perturbation and `threshold_sweep_record` export;
- visible `failed_expectation_report` table;
- plan-aligned `transport_cost_matrix_record` and `xi_residue_mass_record` exports;
- explicit `xi_pressure_penalty` inside object evidence terms;
- guarded `transport_current_edge.total_cost` for cost-summary inspection;
- external DB checksums in package metadata instead of self-hashing the SQLite DB into itself.

The rebuilt output remains `diagnostic_full` and `scientific_run=false`.
