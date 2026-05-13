# Morphosphere v2.9 实施报告：Intervention Policy Sandbox

## 版本定位

v2.9 `intervention_policy_sandbox` 是 v28 Shadow-Evidence Divergence Gate 之后的第一版行动沙盒层。它不进入真实行动，不改写 Evidence，不改写 source facts，而是把 v28 的 confirmed P、shadow overreach、evidence surprise / Xi、emergence alert 转化为可审判的 intervention proposal，并在 sandbox 中进行确定性代理重放。

## 为什么做 v2.9

v25-v28 已经让 Evidence、Shadow、measure field 和 divergence gate 跑通，但系统仍偏被动感知。v2.9 的目标不是让上层命令底层，而是允许系统提出受限行动提案，并用 sandbox replay 验证这些提案是否有助于降低 divergence proxy、提升 precision 或让 Xi surprise 获得更清晰的后续审查路径。

## 核心边界

- `source_facts_rewritten = 0`
- `hot_swap_allowed = 0`
- `intervention_sandbox_only = 1`
- `action_can_modify_evidence = 0`
- `xi_direct_to_pr_allowed = 0`
- 所有 action 都只是 proposal，不是真实行动。
- 所有 replay 都是 shadow/sandbox proxy，不改写 v25/v26/v27/v28 的事实表。

## 新增核心表

| 表 | 行数 | 作用 |
|---|---:|---|
| `v29_intervention_proposal` | 389 | 从 v28 confirmed P / overreach / surprise / emergence 生成行动提案 |
| `v29_policy_candidate` | 4 | 四类 sandbox policy：P 稳定监控、Shadow overreach 抑制、Xi replay、precision sampling |
| `v29_sandbox_replay` | 389 | 每个 proposal 的 sandbox-only 重放结果 |
| `v29_intervention_effect_report` | 389 | 预测收益、风险、effective-information proxy 与后续路由 |
| `v29_action_divergence_outcome` | 389 | action 对 confirmed P、overreach、Xi surprise 的代理影响 |
| `v29_precision_action_hint` | 109 | 针对 precision / surprise 的观察或重放建议 |
| `v29_recipe_trace` | 4 | v29 计算 recipe |
| `v29_acceptance_report` | 16 | 验收结果 |

## 行动类型

### confirmed_p_stability_monitor

针对 v28 confirmed P，测试是否可以安全让渡注意力，或是否具有未来 v30 层级重整化的候选价值。

### shadow_gain_damping

针对 v28 shadow overreach，在 sandbox 中模拟降低 shadow edge gain 或 proximity continuity gain，观察 divergence proxy 是否下降。

### targeted_xi_replay

针对 v28 evidence surprise / Xi，提出 targeted replay 或更高 precision observation 请求。Xi 仍只能 `via_o_candidate_only` 回流，不能直接变 P/R。

### emergence_probe

针对 v28 emergence alert candidate，提出 masking replay 与 proto-O readiness check。

### precision_sampling_request

针对高 divergence window，提出提高采样精度、重放密度或观测质量的请求。

## Acceptance

本地运行：

```bash
cd Morphosphere_v29
./CHECK_BASELINE.sh
python3 active/v29/scripts/check_v29.py --db outputs/m29.db
```

结果：

```text
MORPHOSPHERE_V29_MERGED_ACCEPTANCE: PASS
V29_INTERVENTION_POLICY_SANDBOX_ACCEPTANCE: PASS
SQLite quick_check: ok
```

## 已实施

- v29 DB `outputs/m29.db`
- v29 runtime sidecars `runtime_store/v29/*.jsonl`
- v29 scripts：`run_v29.py`、`check_v29.py`、`query_v29.py`
- `CHECK_BASELINE.sh` 已纳入 v29 检查
- `RUN_EXAMPLES.sh` 已纳入 v29 查询示例
- v29 不改变 v25/v26/v27/v28 表，只复制 v28 为 m29 后追加新表

## 悬置事项

v29 仍然不是实际具身行动系统。悬置事项包括：

1. 真实 physical actuator / lab action 尚未接入。
2. intervention 仍为 deterministic proxy replay。
3. effective information 目前是 proxy，不是严格因果干预量。
4. v28.1 precision weighting 尚未作为独立 DB 层在本包中实现。
5. v30 hierarchical renormalization 仍待构建。

## 结论

v2.9 标志着 Morphosphere 从“被动审判系统”迈向“可提出行动假设的系统”，但仍严格限制在 sandbox 中。它保留了 v28 的审判边界，并为 v30 的 confirmed P 层级重整化和更严格的有效信息计算准备输入。
