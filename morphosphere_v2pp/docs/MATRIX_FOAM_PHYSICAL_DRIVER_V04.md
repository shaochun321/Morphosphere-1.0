# Matrix-Foam Physical Driver v0.4

## Purpose

This layer restores part of the original physical imagination of the project without pretending to have completed final biology.

The original imagination contained a cell sphere with cells embedded in something like foam, matrix, connective tissue, or contractile tissue. Earlier versions represented geometry and transport but did not explicitly store a substrate/foam layer. v0.4 adds an explicit diagnostic proxy for that missing carrier.

## Main tables

```text
substrate_material_region_v04
cell_matrix_contact_v04
foam_edge_state_v04
substrate_stress_tensor_v04
physical_data_source_manifest_v04
physical_sample_stream_v04
physical_driver_mapping_v04
mechanotransduction_event_v04
substrate_to_raw_event_projection_v04
matrix_foam_replay_result_v04
```

## Philosophical boundary

The project principle remains:

```text
information is structured by spacetime and substrate conditions;
information does not first invent spacetime.
```

Therefore, this layer does not overwrite `raw_event_stream`. It stores a material/substrate explanation layer next to the raw event stream and compares projected mechanotransduction values with existing raw events.

## P/R and Xi boundary

v0.4 must not undo the v0.2.2 repair:

```text
P/R remains canonical decomposition before Xi.
R is counter-structure, not residual.
Xi/Xin is unresolved residue after P/R.
Xi cannot directly create P or R.
```

## Physical driver

The package contains a deterministic fixture CSV so local deployment is complete. The same loader can read an external CSV. The manifest records whether a fixture or external source was used.

No real experimental truth is claimed unless a future scientific workflow supplies and validates a real dataset.

## Replay tests

v0.4 includes replay rows for:

```text
baseline_substrate
force_noise_10
force_noise_30
substrate_softening
substrate_stiffening
shear_wave_injection
sensor_dropout
matrix_edge_ablation
external_csv_schema_check
```

These tests do not prove biology. They check whether the substrate/driver layer changes in the expected diagnostic direction without corrupting source facts.
