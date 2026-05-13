# Morphosphere v8.5.3 Validation Summary

perturbation_run_id: `v853_val_81d1f68c`
base_run_id: `v85_diag_e9d24726`
execution_mode: `diagnostic_full`
integrity_check: `ok`
behavioral_acceptance: `6/6`
threshold_sweep_rows: `11`
transport_cost_matrix_record_rows: `900`
xi_residue_mass_record_rows: `9`
failed_expectation_rows: `0`
baseline_fingerprint: `52b7f1a1c3fd9957db67eb0667e2c4c62343cbf944c9563307d22956625584fd`
effect_signature_hash: `b59e05946c671069078c27b5ab0cdc5aaeee1140947df8db1553f9beed2fd0ec`
reproducibility_max_abs_delta: `0`
reproducibility_passed: `True`

| perturbation | metric | baseline | perturbed | delta | pass |
|---|---:|---:|---:|---:|---:|
| signal_shuffle | relation_normalized_entropy | 0.924202 | 1.000000 | 0.075798 | True |
| geometry_shift | mean_geometry_cost | 0.757376 | 0.957376 | 0.200000 | True |
| boundary_flip | rejected_transport_fraction | 0.503333 | 0.653333 | 0.150000 | True |
| masking_injection | mean_o_support_score | 0.720000 | 0.620000 | -0.100000 | True |
| xi_pressure_injection | xi_quarantine_pressure | 0.222222 | 0.422222 | 0.200000 | True |
| threshold_sweep | threshold_sweep_sensitivity | 0.000000 | 0.202222 | 0.202222 | True |

All records are diagnostic-only and forbidden for scientific conclusion or final biology claims.
