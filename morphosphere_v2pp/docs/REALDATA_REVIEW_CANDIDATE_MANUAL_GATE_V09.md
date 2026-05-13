# Real External Physical Data Ingestion + Candidate Patch Manual Review v0.9

This layer follows `shell0_boundary_closure_external_real_data_trial_v0.8`.

It has two goals:

1. Provide a concrete external physical CSV ingestion contract.
2. Build a human-review packet for the v0.7 staged candidate profile without applying it.

## Boundary

- Append-only diagnostic layer.
- Does not rewrite `spacetime_cell`, `information_fiber`, `raw_event_stream`, P/R, Xi, matrix-foam, or device tables.
- Does not apply v0.7 candidate weights automatically.
- Does not allow Xi/Xin to replace P/R.
- Uses `system_clock_entry` alignment through `clock_n` in the external data schema.

## External CSV schema

Required columns:

```text
clock_n,time_s,sensor_id,sensor_kind,x,y,z,force_x,force_y,force_z,optical_intensity,acoustic_pressure,phase,uncertainty
```

The local package contains `external_physical_trial_v09_demo_proxy.csv`, generated from the built-in deterministic fixture. It is schema-compatible but not real experimental data.

## Decision semantics

If `--declare-real-external` is not supplied, the gate remains:

```text
BLOCKED_PENDING_REAL_EXTERNAL_DATA
```

If real external data is supplied and declared, the system may move to:

```text
REAL_DATA_TRIAL_REVIEW_REQUIRED
```

Even then, the candidate patch is not auto-applied.
