# Morphosphere v32 实施报告：Generalized Source Adapter + Scale Contract

生成时间：2026-05-04T00:03:34Z

## 定位

v32 是多源泛化入口层，不重做 v25-v31 的 P/R/Xi、Shadow、Divergence、Sandbox 或 Macro 结果。它把已经存在的外部真实 evidence、shadow prediction、intervention sandbox、macro-node candidate、policy loop 统一登记为 `general_source_event`，并为每类来源绑定 scale contract、coordinate contract 与 window policy。

核心边界：

- 不改写 source facts。
- 不允许 hot-swap。
- 不授权真实行动。
- legacy bottom 只登记为 pending adapter，不自动进入 active pipeline。
- 外部物理数据只登记 future contract，不伪造数据。

## 已新增表

- `v32_run_manifest`
- `v32_source_adapter_registry`
- `v32_scale_contract`
- `v32_coordinate_system_contract`
- `v32_window_policy_contract`
- `v32_general_source_event`
- `v32_adapter_output_mapping`
- `v32_source_reliability_profile`
- `v32_cross_source_normalization_probe`
- `v32_runtime_artifact_manifest`
- `v32_acceptance_report`

## 核心计数

| 表 | 行数 |
|---|---:|
| `v32_source_adapter_registry` | 7 |
| `v32_scale_contract` | 7 |
| `v32_coordinate_system_contract` | 6 |
| `v32_window_policy_contract` | 6 |
| `v32_general_source_event` | 9458 |
| `v32_adapter_output_mapping` | 9458 |
| `v32_source_reliability_profile` | 7 |
| `v32_cross_source_normalization_probe` | 9 |
| `v32_acceptance_report` | 12 / 12 PASS |

## Source kinds

| source_kind | 状态 | 含义 |
|---|---|---|
| `external_ctc_evidence` | active | v25 已重构的真实 CTC 信息点 |
| `shadow_prediction` | active | v26/v28 的 Shadow edge / prediction support |
| `intervention_sandbox` | active | v29 的 sandbox-only intervention proposal |
| `macro_node_candidate` | active | v30 的 candidate-only macro node |
| `policy_loop` | active | v31 的 sandbox-only policy belief loop |
| `legacy_bottom_internal` | pending | 恢复源码中的早期底层，仅登记，不自动启用 |
| `external_physics` | pending | 未来真实物理数据入口，需要单位、尺度、坐标校准 |

## 运行方式

```bash
./CHECK_BASELINE.sh
python3 active/v32/scripts/check_v32.py --db outputs/m32.db
python3 active/v32/scripts/query_v32.py --db outputs/m32.db --source-kind external_ctc_evidence --limit 3
```

## 悬置项

v32 只解决统一入口与尺度契约。尚未实现：

1. legacy bottom prediction adapter 的真实输出。
2. 外部物理数据 adapter 的真实接入。
3. 多尺度 window policy 的自动调参。
4. 内部底层事件与外部 evidence 的同源 divergence stress test。
5. v33 bottom prediction adapter。

## 结论

v32 把 Morphosphere 从单一 CTC evidence chain 推进为多源统一入口框架：来源可以不同，但必须以白盒方式进入 `general_source_event -> scale/coordinate/window contract -> evidence/shadow/divergence pipeline`。这一步为 v33 恢复早期底层作为 prediction source 做准备。
