# Morphosphere State Separation v0.1 Build Report

## 定位

本构建在 v8.5.3 diagnostic physical-freeze 的数据库上新增 `state_separation_v0.1` 诊断层。它的目标不是生成语义标签，而是验证：

```text
底层时空/纤维事件
  -> 新原点 origin anchor
  -> 无语义 latent trajectories
  -> continuity / conservation / phase binding
  -> Xin residual
  -> partial 3D reprojection
```

原则：

```text
information_structure_is_generated_from_spacetime_fiber_events_before_inverse_spacetime_inference
semantic_labels_allowed = false
scientific_run = false
```

## 新增核心脚本

```text
scripts/run_state_separation_core.py
scripts/run_state_separation_acceptance.py
configs/state_separation_v01.json
```

## 新增数据库表

```text
state_core_run_manifest
raw_event_stream
origin_anchor
latent_trajectory
trajectory_event_binding
xin_residue_state
trajectory_reprojection_report
state_separation_noise_sweep
injected_structure_probe
cross_modal_binding_probe
state_separation_test_report
state_separation_artifact_manifest
```

## 构建输出摘要

```text
state_run_id = state_sep_v01_a6a2fdfd9e
raw_event_count = 1500
channel_count = 3
origin_anchor_count = 10
latent_trajectory_count = 5
event_bindings = 1500
accepted_bindings = 1498
xin_residue_count = 2
state_acceptance = 12 / 12
```

## 轨迹平均分

```text
continuity_score = 0.972325
conservation_score = 0.767466
phase_coherence_score = 0.794383
reconstruction_score = 0.889662
residual_mass = 0.135775
```

## 回投测试

```text
baseline_error = 25.360439
trajectory_error = 11.381968
improvement_over_global = 0.551192
passed = True
```

解释：latent trajectories 的 3D 回投误差低于单一全局原点 baseline，说明这些轨迹不是单纯账本记录，而是保留了部分底层 3D 细胞球状态结构。

## 噪声测试

```text
5% noise:  stability = 0.902857, Xin mass = 0.206704
10% noise: stability = 0.886531, Xin mass = 0.233183
20% noise: stability = 0.858776, Xin mass = 0.283449
30% noise: stability = 0.871837, Xin mass = 0.311265
```

解释：5-10% 噪声下 coassignment 仍稳定；高噪声下 Xin residual mass proxy 增加。

## 隐藏结构注入测试

```text
within_correlation = 0.754536
outside_correlation = 0.055509
detection_contrast = 0.699026
detected_as = xi_proto_candidate
passed = True
```

解释：系统在没有语义标签的情况下，把空间相邻细胞群中的持续低频结构识别为 `xi_proto_candidate`，而不是直接吞掉为普通噪声。

## 跨通道相位绑定

```text
probe_count = 15
avg_phase_coherence = 0.925298
accepted_ratio = 1.000000
```

解释：不同 channel type 之间不是靠“这是光/这是声/这是图像”绑定，而是靠 phase / continuity / delay tolerance 做无语义绑定。

## 边界声明

这次构建仍然不是：

```text
scientific_run
final biology
semantic emergence proof
full recurrent neural system
true vestibular organ
```

它只是一个更贴近项目理念的测试底座：验证底层时空事件能否先生成信息结构，再为未来“从信息结构中反推时空”奠基。
