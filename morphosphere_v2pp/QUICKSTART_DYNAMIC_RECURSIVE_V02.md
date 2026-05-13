# Quickstart: dynamic_recursive_v0.2

解压工程包后运行：

```bash
cd morphosphere_dynamic_recursive_v02_package
./run_local_dynamic_recursive.sh
```

该脚本会执行：

```text
1. v8.5.2 SQL acceptance
2. v8.5.3 behavioral acceptance
3. state_separation_v0.1 acceptance
4. rebuild dynamic_recursive_v0.2 layer
5. dynamic_recursive_v0.2 acceptance
```

数据库文件：

```text
outputs/morphosphere_dynamic_recursive_v02_output_database.db
```

核心新增表：

```text
cell_spatial_coordinate_snapshot
information_relative_coordinate_snapshot
clock_binding_record
preneural_node_state
preneural_edge_state
dynamic_origin_anchor_state
dynamic_latent_trajectory_state
trajectory_transition_edge
topdown_feedback_signal
xin_residue_dynamics
recursive_memory_trace
recursive_metric_weight_state
dynamic_free_energy_trace
recursive_iteration_report
recursive_reprojection_report
recursive_acceptance_report
```

注意：本版本仍是 diagnostic_recursive，不是 scientific_run。
