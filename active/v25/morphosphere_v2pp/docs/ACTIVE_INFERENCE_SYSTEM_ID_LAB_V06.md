# Active-Inference / System-Identification External Lab v0.6

## 版本定位

`active_inference_system_identification_external_lab_v0.6` 接在 `device_neutral_preneural_edge_v0.5` 之后。

本版本解决的是一个历史遗留问题：主线中仍存在“经验公式拼凑感”。旧问题可以概括为：

```text
sigmoid(w_transport * transport + w_support * support - w_boundary * boundary + bias)
```

这类权重不能继续被当作物理常数。v0.6 的处理方式不是让机器学习接管主线，而是建立一个只读外部实验室：

```text
主线数据库 -> 只读特征提取 -> 参数拟合 -> Decision Note -> 人工审查/后续 replay
```

## 关键边界

v0.6 不会做这些事情：

```text
不改写 spacetime_cell
不改写 information_fiber
不改写 raw_event_stream
不改写 P/R/Xi 主线表
不让 Xi 顶替 P/R
不让拟合权重自动进入主线
不声称 scientific_run
```

v0.6 只追加这些表：

```text
external_lab_run_manifest_v06
source_fact_digest_v06
system_id_feature_matrix_v06
system_id_parameter_profile_v06
system_id_iteration_trace_v06
active_inference_free_energy_trace_v06
parameter_sensitivity_report_v06
decision_note_v06
adoption_guard_v06
external_lab_acceptance_report_v06
external_lab_artifact_manifest_v06
```

## 特征来源

v0.6 从已经存在的诊断表中提取数值特征：

```text
p_predictive_support_v022
r_counterstructure_v022
xi_boundary_guard_v022
device_pr_evidence_v05
substrate_to_raw_event_projection_v04
mechanotransduction_event_v04
device_edge_tick_state_v05
```

这些特征包括：

```text
prediction_error
continuity_score
conservation_score
phase_coherence_score
memory_coupling
xin_pressure
r_counter_score
device_evidence_score
matrix_projection_confidence
matrix_projection_error_norm
met_gate_probability
device_energy_dissipation_norm
```

## 拟合结果

```text
sample_count = 50
feature_count = 15
train_count = 40
holdout_count = 10

baseline_train_loss = 0.10231980
fitted_train_loss   = 0.00367300

baseline_holdout_loss = 0.05252528
fitted_holdout_loss   = 0.00427949
```

拟合结果写入：

```text
system_id_parameter_profile_v06
```

但状态为：

```text
candidate_not_adopted
```

## Active-Inference proxy

v0.6 还记录一个诊断性的 expected-free-energy proxy：

```text
free_energy_proxy =
    prediction_component
  + complexity_component
  + xi_component
  + r_counter_component
  + entropy_component
  + device_noise_component
```

它不是严格的科学 FEP 证明，只是为了把经验打分迁移到更可审计的“误差 + 复杂度 + 残留/反证压力”表达上。

## 最敏感参数

当前局部敏感度最高的参数为：

```text
- phase_coherence_score: value=1.024219, sensitivity=0.00161858
- conservation_score: value=0.577930, sensitivity=0.00151928
- matrix_projection_error_neg: value=0.779421, sensitivity=0.00125840
- memory_coupling: value=0.500694, sensitivity=0.00113062
- accuracy_inverse_error: value=0.301720, sensitivity=0.00092419
```

## Decision Note

v0.6 生成 `decision_note_v06`，建议：

```text
HOLD_FOR_HUMAN_REVIEW
```

这意味着候选参数不能直接进入主线。进入主线前至少需要：

```text
1. full replay harness 验证；
2. 真实物理数据驱动验证；
3. P/R/Xi 边界审查；
4. 人工 decision note 批准。
```

## 本地运行

```bash
python -S morphosphere_v2pp/scripts/run_active_inference_lab_v06.py \
  --db outputs/morphosphere_active_inference_lab_v06_output_database.db \
  --report-dir morphosphere_v2pp/reports

python -S morphosphere_v2pp/scripts/run_active_inference_acceptance_v06.py \
  outputs/morphosphere_active_inference_lab_v06_output_database.db
```

也可以使用根目录脚本：

```bash
./run_local_active_inference_lab.sh
```
