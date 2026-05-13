# DYNAMIC_RECURSIVE_V02_BUILD_REPORT

## Build identity

```text
package = morphosphere_dynamic_recursive_v02_package
db = outputs/morphosphere_dynamic_recursive_v02_output_database.db
recursive_run_id = dynrec_v02_5dd10f0aa3
parent_state_run_id = state_sep_v01_a6a2fdfd9e
source_run_id = v85_diag_a5dabddb
version = dynamic_recursive_v0.2
execution_mode = diagnostic_recursive
scientific_run = false
semantic_labels_allowed = false
```

## User goals addressed

1. `latent_trajectory` became `dynamic_latent_trajectory_state`.
2. `origin_anchor` became `dynamic_origin_anchor_state`.
3. `Xin` became `xin_residue_dynamics`.
4. The preneural layer became `preneural_node_state` + `preneural_edge_state`.
5. Information coordinates and generating cell coordinates are explicitly separated.
6. `system_clock_entry` is explicitly bound as recursive time source.
7. Top-down feedback is allowed only as sensitivity/gain calibration, not source-fact rewriting.
8. Metric weights are derived from residual statistics instead of a fixed P/R sigmoid.

## Validation

```text
SQLite integrity_check = ok
v8.5.2 SQL acceptance = 21/21 PASS
v8.5.3 behavioral acceptance = 21/21 PASS
state_separation_v0.1 acceptance = 18/18 PASS
dynamic_recursive_v0.2 acceptance = 39/39 PASS
stored recursive_acceptance_report = 20/20 PASS
```

## Counts

```json
{
  "cell_coordinate_snapshots": 500,
  "information_relative_coordinates": 1500,
  "preneural_node_states": 2500,
  "preneural_edge_states": 5000,
  "dynamic_origin_anchor_states": 250,
  "dynamic_latent_trajectory_states": 250,
  "topdown_feedback_signals": 2000,
  "recursive_memory_traces": 2750,
  "xin_residue_dynamics": 87
}
```

## Recursive improvement

```text
prediction_error: 0.109473 -> 0.062833
continuity_score: 0.962544 -> 0.978143
xin_residual_mass: 0.111796 -> 0.079147
free_energy_proxy: 0.528132 -> 0.437863
reprojection_improvement: 0.409401
```

## Xin dynamics

```json
[
  {
    "dynamic_state": "decaying",
    "count": 62,
    "min_residue_mass": 0.055263713526743856,
    "max_residue_mass": 0.21139394268445777,
    "avg_residue_mass": 0.11759930295510006
  },
  {
    "dynamic_state": "held",
    "count": 2,
    "min_residue_mass": 0.22086785318474159,
    "max_residue_mass": 0.2431284343168352,
    "avg_residue_mass": 0.2319981437507884
  },
  {
    "dynamic_state": "proto_origin_candidate",
    "count": 1,
    "min_residue_mass": 0.2689132595768128,
    "max_residue_mass": 0.2689132595768128,
    "avg_residue_mass": 0.2689132595768128
  },
  {
    "dynamic_state": "reintegrated",
    "count": 22,
    "min_residue_mass": 0.12043354051270042,
    "max_residue_mass": 0.18215319719430925,
    "avg_residue_mass": 0.1376286862661679
  }
]
```

## Boundary

This is still a diagnostic prototype. It does not claim final biology, scientific validation, or completed reverse inference from information structure to spacetime.
