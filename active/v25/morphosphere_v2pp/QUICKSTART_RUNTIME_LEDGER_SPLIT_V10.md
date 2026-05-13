# Morphosphere v1.0 Runtime/Ledger Split Quickstart

This release separates runtime state from the SQLite ledger.

## Run the v1.0 layer

```bash
python3 -S morphosphere_v2pp/scripts/run_runtime_ledger_split_v10.py \
  --db outputs/morphosphere_runtime_ledger_v10_output_database.db \
  --runtime-dir runtime_store/v10 \
  --report-dir morphosphere_v2pp/reports

python3 -S morphosphere_v2pp/scripts/run_runtime_ledger_split_acceptance_v10.py \
  outputs/morphosphere_runtime_ledger_v10_output_database.db
```

## External data

To test a real external physical CSV:

```bash
python3 -S morphosphere_v2pp/scripts/run_runtime_ledger_split_v10.py \
  --db outputs/morphosphere_runtime_ledger_v10_output_database.db \
  --runtime-dir runtime_store/v10 \
  --report-dir morphosphere_v2pp/reports \
  --external-csv path/to/real_physical_samples.csv \
  --declare-real-external
```

Required CSV fields:

`clock_n,time_s,sensor_id,sensor_kind,x,y,z,force_x,force_y,force_z,optical_intensity,acoustic_pressure,phase,uncertainty`

## Boundary

- SQLite is ledger/index/provenance, not the high-frequency physical runtime.
- Runtime state is stored in `runtime_store/v10`.
- No external-lab hot-swap is allowed.
- Candidate parameters can only become a frozen calibration profile after real external data, full replay, P/R-Xi boundary audit, source-fact digest check, and human review.
