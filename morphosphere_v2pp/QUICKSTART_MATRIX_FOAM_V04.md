# Morphosphere Matrix-Foam Physical Driver v0.4 Quickstart

This package continues `online_recursive_sensorium_full_replay_v0.3` with an append-only diagnostic layer:

```text
spacetime_cell / information_fiber / raw_event_stream
  -> matrix-foam substrate proxy
  -> physical sample driver
  -> cell-matrix contact + foam edges + stress tensors
  -> mechanotransduction events
  -> projection into raw-event comparison
  -> replay tests
```

Run locally:

```bash
./run_local_matrix_foam.sh
```

Main database:

```text
outputs/morphosphere_matrix_foam_v04_output_database.db
```

The physical driver supports a CSV schema. If no external CSV is supplied, the package writes and uses:

```text
morphosphere_v2pp/data/physical_fixture_v04.csv
```

Boundary:

```text
This layer is diagnostic/proxy. It is not final ECM biology, not a scientific run,
and not a claim of real experimental validation. It does not rewrite source facts.
```

Use an external physical CSV:

```bash
python -S morphosphere_v2pp/scripts/run_matrix_foam_v04.py \
  --db outputs/morphosphere_matrix_foam_v04_output_database.db \
  --report-dir morphosphere_v2pp/reports \
  --physical-csv path/to/your_physical_samples.csv
```

Required CSV columns:

```text
clock_n,time_s,sensor_id,sensor_kind,x,y,z,force_x,force_y,force_z,optical_intensity,acoustic_pressure,phase,uncertainty
```
