# Morphosphere v36.8 Mainline Consolidated Final

本文件是把剩余计划收束到一个统一版本后的总报告。它不再继续拆分 v36.8.4/v36.8.5。

## 定位

- 版本定位：`v36.8_mainline_consolidated_final`。
- 运行性质：全链路主线经验整合 + v36.7 非破坏性硬化基线。
- 不是：online native runtime、旧 DB 破坏性迁移、真实 PDE / 连续场、语义主线系统。

## 统一后的主线链路

```text
raw information point -> coordinate/backprojection -> trajectory/T window -> O/P/R/Xin proxy split -> counter/masking -> external ledger -> attention routing -> hyperedge binding -> variational closure proxy -> Xin carrier/readout boundary -> process_window/native anchor
```

## 角色分布

| role | windows | share | mean P | mean R | mean Xin |
|---|---:|---:|---:|---:|---:|
| XIN_RESIDUAL_PRESSURE | 201 | 0.3778 | 0.5478 | 0.3006 | 0.3179 |
| LOW_OR_MIXED_SIGNAL | 137 | 0.2575 | 0.5593 | 0.2823 | 0.2631 |
| R_COUNTER_PRESSURE | 92 | 0.1729 | 0.5375 | 0.3356 | 0.2614 |
| P_STABLE_SUPPORT | 65 | 0.1222 | 0.6108 | 0.2765 | 0.2224 |
| P_R_MIXED_COMPETITION | 37 | 0.0695 | 0.5825 | 0.3054 | 0.2718 |

## 连续状态转移摘要

| transition | edges | share | mean ΔP | mean ΔR | mean ΔXin |
|---|---:|---:|---:|---:|---:|
| XIN_STAY | 137 | 0.3072 | -0.0015 | -0.0012 | -0.0006 |
| MIXED_STAY | 85 | 0.1906 | -0.0033 | -0.0006 | -0.0010 |
| P_STAY | 72 | 0.1614 | -0.0015 | 0.0019 | -0.0006 |
| R_STAY | 58 | 0.1300 | -0.0049 | 0.0011 | -0.0008 |
| XIN_TO_MIXED | 14 | 0.0314 | -0.0012 | -0.0067 | -0.0010 |
| P_TO_MIXED | 13 | 0.0291 | -0.0164 | -0.0018 | -0.0011 |
| MIXED_TO_XIN | 11 | 0.0247 | -0.0024 | 0.0033 | 0.0000 |
| MIXED_TO_P | 8 | 0.0179 | 0.0099 | -0.0008 | -0.0025 |
| XIN_TO_R | 8 | 0.0179 | -0.0086 | 0.0093 | 0.0001 |
| P_TO_R | 7 | 0.0157 | -0.0276 | 0.0275 | -0.0009 |
| P_TO_XIN | 7 | 0.0157 | -0.0229 | 0.0034 | 0.0003 |
| R_TO_MIXED | 7 | 0.0157 | 0.0114 | -0.0197 | -0.0012 |
| R_TO_XIN | 6 | 0.0135 | 0.0065 | -0.0113 | 0.0003 |
| XIN_TO_P | 6 | 0.0135 | 0.0059 | -0.0053 | -0.0017 |
| R_TO_P | 5 | 0.0112 | 0.0154 | -0.0201 | -0.0018 |
| MIXED_TO_R | 2 | 0.0045 | -0.0031 | 0.0070 | 0.0003 |

## 合并后的工程层定位

- 主线能力：T/O/P/R/Xin、counter/masking、variational closure proxy。
- 路由/绑定：attention、hyperedge、external ledger。
- 证据锚定：native anchor fact、dark-grid zone、process_window FK binding。
- 工程支撑：RMI H2/H3、safe stress guard、semantic quarantine、coordinate invariance CI。
- 外部模块：Xin carrier external readout，仍只读。

## Final gates

| gate | status | observed | required | note |
|---|---|---:|---:|---|
| mainline_trace_full_coverage | PASS | 532 | 532 | Full trajectory-window mainline traces should be consolidated. |
| continuous_transition_edges | PASS | 446 |  >= 400 | Continuous transition graph retained. |
| native_anchor_validation | PASS | 855/855 | 855/855 | All required native anchor materialized refs hit. |
| strict_external_entropy_hit | WARN | 848/855 | 855/855 | Known 7-row strict ledger warning retained; operational refs cover all. |
| safe_stress_guard_rules | PASS | 27 | 27 | Safe stress guard config consolidated. |
| semantic_quarantine_sidecar | PASS | 36 | 36 | Semantic quarantine sidecar retained. |
| rmi_default_index_rows | PASS | 11530 | 11530 | H2/H3 default RMI index retained. |
| rmi_h2_h3_false_neighbor | PASS | 0 | 0 | Default RMI variants must have zero false-neighbor groups in current mixed space. |
| external_readout_boundary | PASS | 31 | 31 | Readout boundary detail retained. |

## Remaining debt

| debt | severity | status | next action |
|---|---|---|---|
| 7 native anchors have operational ledger refs but not strict historical external entropy event hits | WARN | Known and isolated | Keep WARN or synthesize sidecar events with provenance in a later release. |
| Masking influence is still signature-level plus stress-calibration, not full causal proof | MEDIUM | Partially addressed | Run source-level randomized counter/masking interventions if needed. |
| CTC02 upper behavior is same-formula projection/native-shaped replay, not full v35-v36.6 native rerun | MEDIUM | Partially addressed | Build a small full-native replay harness if future work resumes. |
| Online Native Runtime remains out of scope | BLOCKER_FOR_V37_ONLINE | Not claimed | Only after final baseline release should v37.0 runtime prototype begin. |

## 结论

v36.8 consolidated final 将分散数据集中为一个主线经验基线：它保留了 532 条轨迹窗口、446 条连续状态转移、855 条 native anchor facts、27 条 safe stress rules、36 条 semantic quarantine sidecar 记录以及 11,530 条 H2/H3 RMI 默认索引。它的意义是把主线能力、证据锚定、硬化层、外部模块和交付层收束到一个数据包中，避免继续小版本分裂。
