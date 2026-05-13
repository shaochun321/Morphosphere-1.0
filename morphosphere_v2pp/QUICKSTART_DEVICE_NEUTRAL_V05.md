# QUICKSTART: Device-Neutral Preneural Edge v0.5

This package continues `matrix_foam_physical_driver_v0.4` and adds a simulated device-neutral preneural edge layer.

## Run all local checks

```bash
./run_local_device_neutral.sh
```

Main database:

```text
outputs/morphosphere_device_neutral_v05_output_database.db
```

## Rebuild only v0.5

```bash
python3 -S morphosphere_v2pp/scripts/run_device_neutral_v05.py \
  --db outputs/morphosphere_device_neutral_v05_output_database.db \
  --report-dir morphosphere_v2pp/reports

python3 -S morphosphere_v2pp/scripts/run_device_neutral_acceptance_v05.py \
  outputs/morphosphere_device_neutral_v05_output_database.db
```

## What v0.5 adds

```text
matrix_foam / MET events
  -> preneural_device_model_registry_v05
  -> preneural_synaptic_edge_v05
  -> device_edge_tick_state_v05
  -> memristive_plasticity_update_v05
  -> neuromorphic_event_projection_v05
  -> preneural_membrane_state_v05
  -> device_pr_evidence_v05
  -> device_neutral_replay_result_v05
```

The four simulated model families are:

```text
ideal_memristive_edge
noisy_rram_like_edge
volatile_memristive_edge
oect_ionic_edge
```

They are diagnostic proxies only. This version does not claim real hardware behavior, final biology, or scientific validation.

## Boundary

P/R remains before Xi. Device evidence is an evidence channel only; it cannot directly create P, R, or Xi and cannot rewrite source facts.
