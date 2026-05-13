# Morphosphere v8.5.2 Acceptance

Main entrypoint:

```bash
cd morphosphere_v2pp
python run_v85_diagnostic.py
python scripts/run_acceptance_sql.py v85_full_diagnostic_run.db
```

This remains `diagnostic_full`. It does not create v8.6/v9 and does not mark any output as `scientific_run`.

Required acceptance categories:

- SQLite integrity check is ok.
- `run_manifest.execution_mode = diagnostic_full`.
- Confirmation Graph has no invalid transitions and no `masking_supported` synonym.
- Spike/event channel has nonzero, nonuniform `spike_rate`.
- Transport has accepted and rejected rows, nonuniform weights, and nonzero boundary or signal drift.
- O candidates include `formation_mode = derived_minimal`.
- Xi lifecycle includes multiple states beyond held/carry.
- Relation entropy is computed from recorded transport assignment distributions.
- Proxy provenance covers diagnostic/synthetic/proxy components.
- Manifest distinguishes physical, window, and spacetime counts.
- Telemetry report is present.
- Synthetic emergence export remains isolated from production/scientific use.
