# Quickstart: Online Recursive Sensorium + Full Replay Harness v0.3

This package continues `pr_restoration_xi_boundary_v0.2.2` with a clock-ordered online recursive sensorium.

## Run all local checks

```bash
cd morphosphere_online_sensorium_v03_package
./run_local_online_sensorium.sh
```

The packaged database is:

```text
outputs/morphosphere_online_sensorium_v03_output_database.db
```

## Rebuild only v0.3

```bash
cd morphosphere_online_sensorium_v03_package
python -S morphosphere_v2pp/scripts/run_online_sensorium_v03.py \
  --db outputs/morphosphere_online_sensorium_v03_output_database.db \
  --report-dir morphosphere_v2pp/reports

python -S morphosphere_v2pp/scripts/run_online_sensorium_acceptance_v03.py \
  outputs/morphosphere_online_sensorium_v03_output_database.db
```

## Boundary

- `system_clock_entry` is the explicit time source.
- Source facts remain read-only: `spacetime_cell`, `information_fiber`, `raw_event_stream`, coordinate snapshots, and system clock are not rewritten.
- P/R remains before Xi/Xin.
- Xi/Xin is post-P/R unresolved residue and cannot directly create P or R.
- Full replay uses copy-mutated replay buffers, not source-table mutation.
