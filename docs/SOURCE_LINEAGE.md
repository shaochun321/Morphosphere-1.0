# v2.7R short-root Source Lineage Restoration

Root folder: `m/`.

This package restores early Morphosphere source trees as legacy/audit source and keeps v2.5 evidence reconstruction as the active baseline.

Generated: 2026-05-02T19:57:50.964889+00:00

## Restored source trees

- `lin/v853p` from `morphosphere_v853_physical (1).zip`: 105 Python files, status=restored_legacy_audit
- `lin/v853v2` from `morphosphere_mainline_v853_validation_release.zip`: 35 Python files, status=restored_legacy_audit
- `lin/v853pp` from `morphosphere_mainline_v853_validation_release.zip`: 104 Python files, status=restored_legacy_audit
- `lin/v01` from `morphosphere_state_separation_v01_package(1).zip`: 105 Python files, status=restored_legacy_audit
- `lin/v02` from `morphosphere_dynamic_recursive_v02_package(2).zip`: 105 Python files, status=restored_legacy_audit
- `lin/v05` from `morphosphere_device_neutral_v05_package(3).zip`: 105 Python files, status=restored_legacy_audit
- `lin/v08` from `morphosphere_shell0_closure_v08_package(1).zip`: 105 Python files, status=restored_legacy_audit
- `lin/v24` from `morphosphere_ctc_source_verified_v24_full_package(3).zip`: 29 Python files, status=active_history_reference
- `lin/v25` from `ms25_core.zip`: 29 Python files, status=active_history_reference

## Boundary

`legacy source restored` does **not** mean legacy logic is automatically active. Legacy modules are audit/restoration material unless explicitly approved through an adapter and acceptance gate.

## Known unresolved exact directory names

- `morphosphere/stage1_physics`: not_found_in_uploaded_artifacts
- `morphosphere/stage2_object`: not_found_in_uploaded_artifacts
- `morphosphere/runtime/spms`: not_found_in_uploaded_artifacts
- `morphosphere/solvers`: not_found_in_uploaded_artifacts

## Active baseline

- `morphosphere_v2pp/` from v2.5 evidence reconstruction.
- `runtime_store/` from v2.5 runtime sidecars.
- `outputs/morphosphere_evidence_reconstruction_v25_output_database.db`.
