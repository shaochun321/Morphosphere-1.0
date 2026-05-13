# Morphosphere v8.5.3 physical-freeze rebuilt package

This rebuild keeps the v8.5.3 diagnostic boundary and adds alignment hardening: `threshold_sweep_record`, `failed_expectation_report`, `transport_cost_matrix_record`, `xi_residue_mass_record`, explicit DB checksums, and a stdlib-first local runner. Start with `QUICKSTART_V853.md`.

# Morphosphere V2++ (V6 Unified Architecture)

This is the authoritative implementation of the Morphosphere Unified Implementation Spec v6.

## Structure
- `src/morphosphere/active_exec/`: Core generation engine and physics.
- `schemas/`: Versioned JSON Schemas (Draft 2020-12).
- `docs/`: Project documentation, including V8 Execution Paths (`EXECUTION_PATHS.md`).
- `migrations/`: SQLite DB migrations.
- `tests/`: Test suite covering unit, integration, replay, and hard_cases.

## Setup
```bash
pip install -e .
pytest tests/
```
