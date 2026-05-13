# Morphosphere v36.8.3 Mainline Empirical Batch Report

## 1. 版本定位
v36.8.3 不是外围硬化版本，而是主线实证批处理：全量主线轨迹、连续状态转移、masking 分流、CTC01/02 上层对照、attention/hyperedge/variational 贡献拆解、external readout 边界。

## 2. 核心计数
- version: `v36.8.3_mainline_empirical_batch`
- full_trace_windows: `532`
- transition_edges: `446`
- transition_classes: `16`
- role_distribution: `{'P_STABLE_SUPPORT': 65, 'LOW_OR_MIXED_SIGNAL': 137, 'XIN_RESIDUAL_PRESSURE': 201, 'R_COUNTER_PRESSURE': 92, 'P_R_MIXED_COMPETITION': 37}`
- masking_diversion_buckets: `10`
- ctc_upper_metrics: `6`
- module_contribution_rows: `11`
- external_readout_rows: `31`
- external_readout_writes_mainline: `0`
- db_integrity: `ok`

## 3. 角色分布
- XIN_RESIDUAL_PRESSURE: 201
- LOW_OR_MIXED_SIGNAL: 137
- R_COUNTER_PRESSURE: 92
- P_STABLE_SUPPORT: 65
- P_R_MIXED_COMPETITION: 37

## 4. 连续状态转移 Top
- XIN_STAY: 137
- MIXED_STAY: 85
- P_STAY: 72
- R_STAY: 58
- XIN_TO_MIXED: 14
- P_TO_MIXED: 13
- MIXED_TO_XIN: 11
- MIXED_TO_P: 8
- XIN_TO_R: 8
- P_TO_XIN: 7
- R_TO_MIXED: 7
- P_TO_R: 7
- XIN_TO_P: 6
- R_TO_XIN: 6
- R_TO_P: 5

## 5. Masking 分流审计
生成 `v3683_masking_diversion_audit` 与 `v3683_masking_transition_influence`。该结果表明 masking exposure / survival 与 R/Xin 分流存在可量化关联，但仍标记为 signature-level association，不宣称因果证明。

## 6. CTC01/02 上层对照
继承 Pass17 的 same-formula / no-retuning 投影，并在本版集中为上层主线对照表。
- attention_tension_proxy: seq01=0.390988, seq02=0.380644, delta=-0.010344
- hyperedge_arity_proxy: seq01=7.734440, seq02=7.580756, delta=-0.153684
- action_score_proxy: seq01=0.525392, seq02=0.523806, delta=-0.001586
- xin_var_proxy: seq01=0.343256, seq02=0.334565, delta=-0.008691
- projected_rband_candidate: seq01=0.842324, seq02=0.752577, delta=-0.089746
- projected_xin_carrier_needed: seq01=1.000000, seq02=1.000000, delta=0.000000

## 7. 模块贡献拆解
`v3683_module_contribution_decomposition` 将模块分为主线状态改变、证据锚定、治理约束、关系绑定、外部只读、工程支撑等类别，防止把 RMI/guard/部署工具误认为 T/O/P/R/Xin 主线能力。

## 8. External readout 边界
- external readout rows: 31
- writes_mainline: 0
- mainline_semantic_fields_present: 0
结论：external readout 仍是只读解释层。

## 9. Acceptance
- all 532 trajectory windows in full trace: **PASS** — 532 windows
- continuous transition graph nonempty: **PASS** — 446 edges
- role transition summary exists: **PASS** — 16 classes
- masking diversion audit generated: **PASS** — 10 buckets
- CTC01/02 upper comparison present: **PASS** — 6 metrics; ctc_att rows 532
- module contribution classification present: **PASS** — 11 modules
- external readout remains read-only: **PASS** — writes=0; semantic_fields=0
- RMI/guard/anchor are support not mainline truth: **PASS** — boundary encoded in module contribution decomposition

## 10. 下一步
下一批不应继续拆小版本，建议做 `v36.8.4 Mainline Causal Batch`：source-level masking/counter intervention, trajectory-continuous P/R/Xin causal response, CTC02 native-shaped upper replay expansion, and readout competence audit.