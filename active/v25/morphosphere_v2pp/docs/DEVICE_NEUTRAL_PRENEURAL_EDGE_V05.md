# Device-Neutral Preneural Edge v0.5

## Purpose

`device_neutral_preneural_edge_v0.5` inserts a simulated, device-neutral pre-neural edge layer between the matrix-foam physical driver and the online sensorium.

The point is not to claim that the project now contains real memristors or real organic electrochemical transistors. The point is to define a stable interface where future neuromorphic components can be simulated, swapped, perturbed, and audited without breaking the main chain.

## Main chain

```text
matrix_foam_physical_driver_v0.4
  -> foam_edge_state_v04
  -> mechanotransduction_event_v04
  -> preneural_synaptic_edge_v05
  -> device_edge_tick_state_v05
  -> preneural_membrane_state_v05
  -> device_pr_evidence_v05
```

## Device models

The registry contains four simulated device families:

```text
ideal_memristive_edge
noisy_rram_like_edge
volatile_memristive_edge
oect_ionic_edge
```

Each model has diagnostic parameters:

```text
g_min / g_max
volatility
hysteresis
retention_decay
read_noise / write_noise
update_gain
ionic_lag
energy_scale
```

These are not calibrated device constants. They are local diagnostic parameters used to test whether the pre-neural edge protocol can support memory, plasticity, noise, hysteresis, and fault response.

## Boundary rules

```text
1. Source facts are append-only and read-only.
2. Device evidence cannot directly create P.
3. Device evidence cannot directly create R.
4. Device evidence cannot directly create Xi.
5. P/R remains the canonical decomposition before Xi.
6. Xi remains unresolved post-P/R residue.
7. No semantic labels are used in device-edge updates.
8. No real hardware behavior is claimed.
```

## Why this matters

Earlier project stages had a gap between a physically richer substrate and a neural-like recursive layer. v0.5 begins to fill that gap with simulated edge dynamics:

```text
conductance
memory state
hysteresis
retention loss
read/write noise
plasticity update
energy dissipation proxy
```

This lets future work test neuromorphic-like behavior without allowing hardware metaphors to overtake the ontology.

## Replay scenarios

The v0.5 replay harness includes:

```text
baseline_device
read_noise_10
read_noise_30
write_noise_30
retention_loss
edge_stuck_on
edge_stuck_off
oect_slow_ionic
rram_burst_noise
device_model_swap_all_ideal
```

The expected behavior is not that all perturbations preserve perfect P support. The expected behavior is that noise and faults reduce P stability, increase R/Xi pressure, and never rewrite source facts.
