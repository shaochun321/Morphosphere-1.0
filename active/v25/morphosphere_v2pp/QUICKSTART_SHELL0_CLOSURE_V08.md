# Morphosphere Shell0 Boundary Closure v0.8 Quickstart

This package extends `candidate_adoption_gate_real_data_calibration_v0.7` with an append-only diagnostic layer:

- Shell0 multi-resolution boundary closure probes
- Contact/matrix-edge ablation trials
- Ghost-shell negative controls
- External real-data trial schema and fixture mapping
- Candidate patch review without automatic adoption

Run v0.8 checks:

```bash
python3 -S morphosphere_v2pp/scripts/run_shell0_closure_acceptance_v08.py \
  outputs/morphosphere_shell0_closure_v08_output_database.db
```

Rebuild v0.8 layer:

```bash
python3 -S morphosphere_v2pp/scripts/run_shell0_closure_v08.py \
  --db outputs/morphosphere_shell0_closure_v08_output_database.db \
  --report-dir morphosphere_v2pp/reports
```

Use a real external data CSV:

```bash
python3 -S morphosphere_v2pp/scripts/run_shell0_closure_v08.py \
  --db outputs/morphosphere_shell0_closure_v08_output_database.db \
  --report-dir morphosphere_v2pp/reports \
  --external-csv path/to/real_physical_samples.csv \
  --declare-real-external
```

The expected CSV columns are:

```text
clock_n,time_s,sensor_id,sensor_kind,x,y,z,force_x,force_y,force_z,optical_intensity,acoustic_pressure,phase,uncertainty
```

Boundary: v0.8 does not auto-apply candidate weights, does not rewrite source facts, and does not promote Shell0 into a confirmed physical layer.
