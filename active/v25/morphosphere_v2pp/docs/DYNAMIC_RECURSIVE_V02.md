# Morphosphere dynamic_recursive_v0.2

## 目标

本版本在 `state_separation_v0.1` 的基础上继续推进首要目标：

```text
把 latent_trajectory、origin_anchor、Xin 和前神经系统做成动态递归系统。
```

本版本仍然遵守项目的物理优先原则：

```text
信息结构是被时空结构出来的；
本版本不启用“从信息结构反推时空”的科学主张；
reverse spacetime inference 仍处于后续阶段。
```

## 本版本新增链路

```text
raw_event_stream
  + separated cell_spatial_coordinate_snapshot
  + information_relative_coordinate_snapshot
  + system_clock_entry
    ↓
preneural_node_state / preneural_edge_state
    ↓
dynamic_origin_anchor_state
    ↓
dynamic_latent_trajectory_state
    ↓
topdown_feedback_signal
    ↓
xin_residue_dynamics
    ↓
recursive_memory_trace
    ↓
recursive_reprojection_report / recursive_acceptance_report
```

## 对用户关键要求的处理

### 1. 信息坐标与产生信息的细胞坐标分开存储

本版本新增两张表：

```text
cell_spatial_coordinate_snapshot
information_relative_coordinate_snapshot
```

`cell_spatial_coordinate_snapshot` 保存产生信息的细胞在底层物理时空中的位置、法向、边界距离、支撑半径等。

`information_relative_coordinate_snapshot` 保存每条 raw event 相对于 `origin_anchor` 的相对坐标、相对相位与径向距离。

这意味着：

```text
细胞几何位置 ≠ 信息相对位置
```

程序层面不再只依赖 raw_event_stream 中的坐标缓存。raw event 的 x/y/z 可被视为事件携带的来源坐标副本，而不是信息结构的唯一坐标本体。

### 2. 系统时钟作为时间源

旧库中 `system_clock` 表为空，但 `system_clock_entry` 表是实际可用系统时钟源。本版本显式记录：

```text
clock_source_table = system_clock_entry
clock_count = 10
min_clock_n = 0
max_clock_n = 9
dt_s = 0.01
```

并在 `clock_binding_record` 中声明：

```text
system_clock_entry is the explicit time source for recursive dynamics;
empty system_clock is not used as source-of-truth.
```

### 3. 前神经系统动态递归化

新增：

```text
preneural_node_state
preneural_edge_state
```

每个前神经节点跨 clock 与 iteration 更新：

```text
activation = f(input_energy, recurrent_activation, topdown_sensitivity, memory_state, uncertainty)
```

每条边跨 clock 与 iteration 更新：

```text
recurrent_weight = f(spatial_distance, phase_lag, activation, edge_memory)
```

这仍是诊断原型，但它已经不再只是一次性表记录。

### 4. latent_trajectory 动态化

新增：

```text
dynamic_latent_trajectory_state
trajectory_transition_edge
```

每条轨迹跨系统时钟更新：

```text
centroid
velocity
phase
continuity_score
conservation_score
phase_coherence_score
prediction_error
xin_residual_mass
memory_coupling
```

### 5. origin_anchor 动态化

新增：

```text
dynamic_origin_anchor_state
```

动态原点不再只是 v0.1 中的一次性 anchor，而是由前神经节点活动、轨迹支撑域和递归记忆共同更新。

### 6. Xin 动态化

新增：

```text
xin_residue_dynamics
```

Xin 不再只是静态残留账本，而是有动态状态：

```text
decaying
held
proto_origin_candidate
reintegrated
```

### 7. 上层反馈的边界

新增：

```text
topdown_feedback_signal
```

但反馈只能调节：

```text
sensitivity / gain / memory coupling
```

不能改写：

```text
raw_event_stream
spacetime_cell
information_fiber
```

也就是：

```text
top-down calibration allowed;
top-down source fact rewrite forbidden.
```

## 验证结果

```text
v8.5.2 SQL acceptance: 21 / 21 PASS
v8.5.3 behavioral acceptance: 21 / 21 PASS
state_separation_v0.1 acceptance: 18 / 18 PASS
dynamic_recursive_v0.2 acceptance: 39 / 39 PASS
stored recursive_acceptance_report: 20 / 20 PASS
```

## 关键指标

```text
raw_event_count = 1500
system_clock_entry count = 10
cell_coordinate_snapshots = 500
information_relative_coordinates = 1500
preneural_node_states = 2500
preneural_edge_states = 5000
dynamic_origin_anchor_states = 250
dynamic_latent_trajectory_states = 250
topdown_feedback_signals = 2000
recursive_memory_traces = 2750
xin_residue_dynamics = 87
```

递归过程：

```text
prediction_error: 0.109473 -> 0.062833
xin_residual_mass: 0.111796 -> 0.079147
free_energy_proxy: 0.528132 -> 0.437863
reprojection improvement: 0.409401
transition_acceptance_ratio: 0.977778
```

## 仍然不能声称的事情

本版本不是：

```text
scientific_run
final biology
真实前庭器官
完整类神经系统
语义涌现证明
从信息结构反推真实时空的完成版本
```

它完成的是：

```text
把 v0.1 的一次性状态分离结果推进成跨系统时钟、跨递归迭代的动态诊断原型。
```
