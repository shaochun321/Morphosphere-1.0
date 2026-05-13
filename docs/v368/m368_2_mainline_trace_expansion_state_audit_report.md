# Morphosphere v36.8.2 Mainline Trace Expansion + State Transition Audit

## 定位

v36.8.2 回到主线功能，不新增外围硬化对象。本轮从现有全链路物化数据中扩展样本级主线轨迹，并审计 T/O/P/R/Xin 状态变化原因、masking 对 R/Xin 分流的实际关系、attention/hyperedge/variational 的上层作用，以及 external readout 的只读边界。

本轮不是 online runtime，也不是旧 DB 迁移。旧 DB 不被修改。

## 核心计数

| 项目 | 数量 |
|---|---:|
| expanded mainline traces | 200 |
| state transition reason rows | 200 |
| masking signatures audited | 1 |
| attention coupling rows | 120 |
| hyperedge/variational coupling rows | 120 |
| external readout boundary rows | 31 |
| CTC02 trajectory windows | 291 |
| failed acceptance | 0 |

## Expanded trace role distribution

| role proxy | count |
|---|---:|
| MIXED_SUPPORT_COUNTER_RESIDUAL | 81 |
| XIN_RESIDUAL_PRESSURE | 48 |
| R_COUNTER_PRESSURE | 35 |
| P_STABLE_SUPPORT | 25 |
| UNSTABLE_MIXED_WINDOW | 11 |

## 主线状态变化解释

本轮把每条样本 trace 的角色变化原因写入 `v3682_state_transition_reason_audit`。核心 driver 包括：

- `p_measure_value`: 稳定支撑代理强，R/Xin 低于普通区间。
- `r_measure_value`: 反证压力进入上四分位。
- `xi_residual_mass`: 残余压力进入上四分位。
- `masking_exposure_gain`: 屏蔽暴露增益高，R/Xin 更容易从背景进入审计。
- `entropy_violation_mass`: 外部账本闭合压力增加。
- `p_displacement_mass`: P 支撑受到位移挑战。

这些是数理代理，不是语义标签。

## Masking 效应

`v3682_masking_effect_audit` 按 masking signature 聚合 P/R/Xin 均值、masking exposure gain 与 entropy violation mass。它用于判断 masking 是否只是记录字段，还是和 R/Xin 分流存在统计关系。

当前结论：masking 是主线调制器，但仍需要 source-level masking rerun 才能从相关性升级为因果证据。

## Attention / Hyperedge / Variational 的主线定位

- attention: 改变资源分配状态，不授权真实行动。
- hyperedge: 绑定多主体共现事件，不宣称本体关系。
- variational/Xin_var: 把局部差分提升为路径级账本闭合缺陷代理，不是真实物理最小作用量。

## External readout 边界

`v3682_external_readout_boundary_audit` 检查 Xin carrier readout 的 `writes_mainline` 与 `mainline_semantic_fields_present`。本轮失败数为 0。

## 模块分类

`v3682_module_state_change_classification` 将模块分为：主线状态变化、证据锚、治理账本、外部边界、工程索引、runtime guard。RMI、safe stress guard、native anchor 不被计作新的 T/O/P/R/Xin 主线能力。

## 下一步建议

v36.8.3 应优先做：

1. 对 200 条 expanded trace 做连续窗口状态转移图，而不只是单窗口角色分布。
2. 对 masking 做 source-level rerun 对照，区分 masking causality 和 signature correlation。
3. 对 CTC02 扩展 attention/hyperedge/variational 的真实 replay，而非仅投影。
4. 对 external readout 评估解释有效性边界：哪些 Xin family 被区分，哪些只是通用 capacity gap。
