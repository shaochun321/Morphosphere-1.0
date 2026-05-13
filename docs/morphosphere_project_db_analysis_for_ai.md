# Morphosphere v36.6 / Pass14 项目与 DB 分析文档（给其他 AI 阅读）

- 生成时间：2026-05-06T13:15:15.499105Z
- 分析对象：`Morphosphere_v36_6_complete_deploy_pass14.tar.zst` 及其关键 SQLite DB。
- 重要声明：当前项目是 **full-chain materialized integration + native-shaped replay**，不是在线生命 runtime，也不是完整真实 PDE/连续场求解器。

## 1. 一句话定义

Morphosphere 当前是一个面向“信息时空轨迹”的离线工程系统：它把外部/底层信息点转成坐标回投、轨迹窗口、T/O/P/R/Xin 测度、反证/屏蔽、外部熵账本、attention、hyperedge、variational action、Xin carrier 与 external readout，并用 `process_window` 把这些对象统一成可查询、可回溯、可审计的全链路数据结构。

它不是语义分类器，也不是单纯细胞追踪器；更像是一个 **可审计的认知/信息过程账本与轨迹分解框架**。

## 2. 现在项目到底是什么

### 2.1 核心对象

- **信息点（information point）**：外部/底层观测被整理成最小信息单位。
- **三维/四维回投**：信息点保留 frame、track、坐标、归一化/相对坐标和 trajectory window 的回投链。
- **信息时空轨迹**：信息点跨窗口、支撑域和过程算子形成的候选轨迹，不等同于语义事件。
- **T/O/P/R/Xin**：上层分解机制。T 是 trace/trajectory/time-window，O 是 support/object candidate，P 是稳定支撑，R 是反证/反结构，Xin 是无法闭合但不能删除的残余。
- **外部熵账本**：治理/审计层，记录等效能量、耗散、噪声、异常、闭合差额；不是物理自由能本体。
- **attention / hyperedge / variational**：上层治理结构，用来决定看哪里、多主体如何绑定、路径账本一致性如何评分。
- **Xin carrier / external readout**：主线只保留 minimal carrier；外部模块只读解释，不得反写主线。
- **process_window**：v36.6 的主线工作单位，绑定 information / time / support-space / process / envelope / ledger。

### 2.2 当前实现形态

当前不是一次从底层物理源在线演化到上层的 runtime，而是：

```text
历史 base DB + runtime_store + v35-v36.5 overlay
-> 全链路全量物化整合
-> process_window 统一索引
-> 上层实证分析
-> 压力投影 / native-shaped replay 样本
```

因此更准确的名称是：**全链路全量数据物化整合运行 + 样本级 native-shaped replay**。

## 3. 对行业来说，它可能有什么作用

当前 AI/Agent 行业正从“只看模型输出”转向“要能追踪、审计、治理和解释整条链路”。企业 AI Agent 的治理、可观测性、数据 lineage、合规审计和安全边界已经成为重点。Morphosphere 的行业位置可以理解为：

1. **AI/Agent observability 的底层思想实验**：不是只记录 prompt/response，而是把信息从来源、轨迹、残余、反证、外部账本到 readout 的全过程结构化。
2. **数据 lineage + AI governance 的实验性融合**：它不只保存数据 lineage，还保存“为什么该看这里、为什么是 P/R/Xin、为什么不能反写主线”的治理痕迹。
3. **面向科学/复杂系统数据的白盒中间层**：适合探索细胞运动、物理观测、传感数据、异常检测、反证链、候选轨迹解释等。
4. **不是替代现有 MLOps/LLMOps 平台**：它目前没有在线 serving、模型训练、生产级 IAM、实时 agent control。它更像一个研究型数据/认知过程 ledger。

行业价值主要在：**可追溯、可回投、可审计、可区分事实/代理/外部解释**。短板在：它不是生产级 agent observability 平台，也不是完整 scientific simulator。

## 4. 当前能识别/分离什么

### 4.1 能识别

- 可追踪信息过程：哪些点能形成 trajectory window。
- 稳定支撑 P：哪些窗口/支撑域表现为相对稳定。
- 反证压力 R：哪些窗口对 P 产生 counter-pressure。
- Xin 残余：哪些信息不能闭合但不能丢弃。
- attention-worthy 区域：哪些区域值得继续看。
- 高阶共同参与事件：哪些 P/R/Xin/mask/ledger/proxy 被同一 hyperedge 绑定。
- 账本一致性路径：哪些 candidate path 在 S_IE_proxy 下更不闭合或更稳定。
- 外部只读解释对象：哪些 Xin carrier 可由 external readout 解释但不能反写主线。

### 4.2 能分离

- 坐标事实轨迹 vs 信息/测度轨迹。
- P 稳定支撑 vs R 反证结构。
- R 反证链 vs Xin 不可闭合残余。
- 噪声/低结构扰动 vs 高结构残余。
- 主线 carrier vs 外部 readout。
- 普通二元关系 vs hyperedge 高阶共同参与事件。

### 4.3 当前数据表现

上层实证分析表明，当前底层数据偏稳定：P/R/Xin 多数是候选级/低风险分离，不是强新异爆发场景。压力投影和 replay 表明，在 counter boost、Xin spike、masking failure 场景下，R/Xin 的状态会显著变化。

## 5. 关键 DB 总览

| DB | 大小MB | 表数 | 非空表 | 估计行数 | 作用 |
|---|---:|---:|---:|---:|---|
| `outputs/m25.db` | 26.32 | 346 | 321 | 65068 | v25 Evidence Reconstruction / information point, coordinate transform, trajectory window, P/R/Xin measures |
| `outputs/m34.db` | 88.71 | 444 | 419 | 204933 | v34 Full base governance / proxy + external entropy control plane on cumulative base |
| `outputs/m35.db` | 0.25 | 14 | 14 | 1087 | v35 Attention proposal + path-integral audit overlay |
| `outputs/m35H.db` | 0.26 | 8 | 8 | 1879 | v35H Hyperedge incidence sidecar |
| `outputs/m36.db` | 0.16 | 11 | 11 | 650 | v36 Dissipative source / information-energy metric proxy |
| `outputs/m361.db` | 0.18 | 11 | 11 | 865 | v36.1 Variational external ledger bridge |
| `outputs/m362.db` | 0.18 | 11 | 11 | 759 | v36.2 Variational action revision / Xin_var bridge |
| `outputs/m363.db` | 0.21 | 11 | 11 | 1010 | v36.3 R spacetime band / Xin continuity bridge |
| `outputs/m364.db` | 0.25 | 12 | 12 | 1457 | v36.4 Constrained coupler / R-band / Xin triage bridge |
| `outputs/m365.db` | 0.21 | 12 | 12 | 269 | v36.5 Semantic stripping + Xin carrier + external readout overlay |
| `outputs/m365_full_rebase.db` | 0.04 | 5 | 5 | 89 | v36.5 full-lineage rebase manifest / coverage / boundary proof |
| `outputs/v366/m365_full_chain_materialized.db` | 11.87 | 24 | 24 | 32224 | Full-chain materialized integration index |
| `outputs/v366/m366_process_window_pass3.db` | 11.09 | 28 | 28 | 37905 | v36.6 process_window + hypernode spacetime backprojection |
| `outputs/v366/m366_implementation_coverage_audit.db` | 0.08 | 6 | 6 | 169 | Implementation coverage / maturity audit |
| `outputs/v366/m366_upper_layer_empirical.db` | 0.62 | 22 | 22 | 1318 | Upper-layer empirical analysis |
| `outputs/v366/m366_build_pass12_execution.db` | 1.8 | 7 | 7 | 6967 | Native-shaped skeleton + offline stress projection |
| `outputs/v366/m366_build_pass13_native_replay.db` | 3.36 | 14 | 14 | 8951 | Sample native-shaped replay / perturbation comparison |

## 6. 核心对象计数

### 6.1 v25 底层 evidence / trajectory / P-R-Xin

| object | count |
| --- | --- |
| information_point_v25 | 4575 |
| coordinate_transform_trace_v25 | 4575 |
| trajectory_window_trace_v25 | 532 |
| p_spacetime_measure_v25 | 532 |
| r_counter_measure_v25 | 532 |
| xi_residual_surface_v25 | 532 |
| decision_evidence_bundle_v25 | 532 |
| attention_yield_event_v25 | 262 |


### 6.2 v35 attention verdict

| verdict | count |
| --- | --- |
| NEUTRAL | 79 |
| EFFECTIVE | 26 |
| INEFFECTIVE | 10 |
| NOVELTY_DISCOVERED | 5 |


### 6.3 v35H hyperedge arity

| hyperedges | avg_arity | min_arity | max_arity |
| --- | --- | --- | --- |
| 120 | 7.125 | 7 | 8 |


### 6.4 v36 metric / dissipative proxy

| object | count |
| --- | --- |
| dissipative_source_registry | 80 |
| delta_xin_field | 64 |
| information_energy_metric_proxy | 160 |
| metric_anchor_audit | 160 |
| curvature_proxy | 120 |


### 6.5 v36.2 variational action / Xin_var

| object | count |
| --- | --- |
| functional_candidates | 5 |
| candidate_paths | 120 |
| discrete_action_scores | 120 |
| stationarity_defect_proxy | 120 |
| xin_var_closure_defect | 120 |
| delta_xin_fallback | 120 |


### 6.6 v36.5 Xin carrier / readout

| object | count |
| --- | --- |
| xin_minimal_carriers | 31 |
| external_xin_definitions | 6 |
| external_semantic_readouts | 31 |
| readout_backwrite_blocks | 4 |
| xin_reentry_policies | 2 |


### 6.7 v36.6 process_window

| object | count |
| --- | --- |
| process_windows | 1633 |
| process_window_members | 22128 |
| hypernode_spacetime_backprojection | 855 |
| hyperedge_spacetime_relations | 2625 |
| coordinate_nonlocal_proxy_audit_examples | 50 |


### 6.8 process_window materialization confidence

| materialization_confidence_class | count |
| --- | --- |
| low_materialization_confidence | 842 |
| medium_materialization_confidence | 671 |
| high_materialization_confidence | 120 |


### 6.9 implementation maturity

| maturity_level | concept_count | evidence_rows |
| --- | --- | --- |
| BLUEPRINT_ONLY | 5 | 0 |
| DATA_POPULATED | 8 | 3691 |
| MATERIALIZED_INDEX | 13 | 30049 |
| NATIVE_RUN_GENERATED | 29 | 24131 |
| SCHEMA_ONLY | 1 | 6 |


## 7. 上层实证发现

| finding_kind | statement | evidence_count |
| --- | --- | --- |
| recognition | The current bottom-to-middle layer recognizes 532 trajectory windows from 4,575 information points and splits each into P/R/Xin measures. | 532 |
| separation | P is mostly candidate-level stable support, R is mostly low but measurable counter-pressure, and Xin is low/decaying but ledger-retained. | P:532 R:532 Xin:532 |
| attention | v35 attention mostly returns NEUTRAL, with 26 EFFECTIVE and 5 NOVELTY_DISCOVERED cases. | 120 |
| hyperedge | v35H hyperedges average >7 nodes and therefore express multi-subject binding rather than binary edges. | 120 hyperedges / 855 incidence |
| variational | v36.2 computes action proxies, stationarity defects, and Xin_var for 120 candidate paths; delta-Xin is only fallback. | 120 |
| rband | R-band/coupler layers build pseudo-continuity candidates and triage Xin into foreground/background/deferred/thermalized/external leakage classes. | 90 bands / 85 triage |
| readout | v36.5 preserves Xin as minimal carriers and external readout remains read-only with blocked backwrite attempts. | 31 carriers / 31 readouts |


### 7.1 T/O/P/R/Xin role proxy 分布

| role_proxy | window_count | percentage | mean_p | mean_r | mean_xin |
| --- | --- | --- | --- | --- | --- |
| XIN_RESIDUAL_PRESSURE | 201 | 0.3778 | 0.5478 | 0.3006 | 0.3179 |
| LOW_OR_MIXED_SIGNAL | 137 | 0.2575 | 0.5593 | 0.2823 | 0.2631 |
| R_COUNTER_PRESSURE | 92 | 0.1729 | 0.5375 | 0.3356 | 0.2614 |
| P_STABLE_SUPPORT | 65 | 0.1222 | 0.6108 | 0.2765 | 0.2224 |
| P_R_MIXED_COMPETITION | 37 | 0.0695 | 0.5825 | 0.3054 | 0.2718 |


### 7.2 Pass12 离线压力投影

| stress_name | trajectory_windows | p_to_r_projected | r_or_p_to_xin_projected | stable_retained | boundary_blocked |
| --- | --- | --- | --- | --- | --- |
| coordinate jitter | 532 | 1 | 0 | 531 | 0 |
| support dropout | 532 | 23 | 0 | 509 | 0 |
| counter-evidence boost | 532 | 513 | 0 | 19 | 0 |
| Xin residual spike | 532 | 1 | 462 | 69 | 0 |
| masking failure | 532 | 450 | 67 | 15 | 0 |
| semantic backwrite attack | 532 | 0 | 0 | 0 | 532 |


### 7.3 Pass13 native-shaped replay 状态转移

| scenario_id | transition_class | count | pct |
| --- | --- | --- | --- |
| baseline | stable_retained | 70 | 1.0 |
| coordinate_jitter | observe_retain_shift | 7 | 0.1 |
| coordinate_jitter | stable_retained | 63 | 0.9 |
| counter_boost | P_or_stable_to_R_focus | 66 | 0.9429 |
| counter_boost | stable_retained | 4 | 0.0571 |
| masking_failure | P_or_stable_to_R_focus | 24 | 0.3429 |
| masking_failure | observe_retain_shift | 13 | 0.1857 |
| masking_failure | stable_retained | 33 | 0.4714 |
| semantic_attack | semantic_backwrite_blocked | 70 | 1.0 |
| support_dropout | P_or_stable_to_R_focus | 1 | 0.0143 |
| support_dropout | observe_retain_shift | 13 | 0.1857 |
| support_dropout | stable_retained | 56 | 0.8 |
| xin_spike | R_or_P_to_Xin_escalation | 69 | 0.9857 |
| xin_spike | stable_retained | 1 | 0.0143 |


## 8. DB 关系边（给 AI 的逻辑图）

| From | To | 关系说明 |
|---|---|---|
| `source/envelope` | `information_point_v25` | source data is converted into information points |
| `information_point_v25` | `coordinate_transform_trace_v25` | each information point receives coordinate/backprojection traces |
| `information_point_v25` | `trajectory_window_trace_v25` | information points are grouped/stiched into trajectory windows |
| `trajectory_window_trace_v25` | `p_spacetime_measure_v25` | trajectory window yields P stable-support measure |
| `trajectory_window_trace_v25` | `r_counter_measure_v25` | trajectory window yields R counter-evidence measure |
| `trajectory_window_trace_v25` | `xi_residual_surface_v25` | trajectory window yields Xi/Xin residual surface |
| `P/R/Xin measures` | `decision_evidence_bundle_v25` | evidence bundles preserve the decision trace |
| `P/R/Xin measures` | `v35_attention_region_index` | regions are indexed as attention candidates |
| `v35_attention_region_index` | `v35_attention_proposal` | attention sandbox proposes where to focus |
| `v35_attention_proposal` | `v35_attentional_path_integral_audit` | external ledger path audit scores attention path |
| `v35_attention_proposal` | `v35h_hyperedge_proposal` | attention events become high-order hyperedge proposals |
| `v35h_hyperedge_proposal` | `v35h_hyperedge_incidence` | hyperedge incidence binds multiple P/R/Xi/mask/ledger/proxy nodes |
| `hyperedge/path` | `v362_candidate_path_inventory` | candidate information-spacetime paths are assembled |
| `v362_candidate_path_inventory` | `v362_discrete_action_score` | paths are scored via S_IE_proxy |
| `v362_discrete_action_score` | `v362_xin_var_closure_defect` | unclosed variational residual becomes Xin_var proxy |
| `R/Xin paths` | `v363_r_spacetime_band_candidate` | R continuity is approximated as spacetime bands |
| `R-band/Xin` | `v364 coupling/triage tables` | coupler triages paths and Xin residual classes |
| `Xin residual` | `v365_xin_minimal_carrier_state` | semanticless mainline stores minimal Xin carriers |
| `v365_xin_minimal_carrier_state` | `v365_external_semantic_readout_result` | external readout interprets carriers read-only |
| `all layers` | `v366_process_window_registry` | process_window is the materialized index joining information/time/support/process/envelope/ledger |
| `v35H hypernodes` | `v366_hypernode_spacetime_backprojection` | hypernodes are backprojected to spacetime as direct/proxy/inferred audit |
| `materialized data` | `pass12/pass13 replay DBs` | stress and native-shaped replay evaluate P/R/Xin behavior under scenarios |

## 9. 关键表结构摘要

### `outputs/m25.db`

v25 Evidence Reconstruction / information point, coordinate transform, trajectory window, P/R/Xin measures

| table | rows | columns |
| --- | --- | --- |
| full_replay_event_buffer_v03 | 13500 | replay_event_id, scenario_id, original_event_id, clock_n, original_node_id, replay_node_id, channel_type, original_value, replay_value, original_phase |
| preneural_edge_state | 5000 | edge_state_id, recursive_run_id, iteration_n, clock_n, source_preneural_node_id, target_preneural_node_id, spatial_distance, phase_lag, recurrent_weight, conduc |
| coordinate_transform_trace_v25 | 4575 | transform_id, source_point_id, from_coordinate_system, to_coordinate_system, raw_x, raw_y, raw_z, normalized_x, normalized_y, normalized_z |
| information_point_v25 | 4575 | point_id, source_id, source_dataset, source_sequence, source_frame, source_track_id, sample_id, sensor_id, sensor_kind, clock_domain |
| recursive_memory_trace | 2750 | memory_id, recursive_run_id, iteration_n, clock_n, memory_scope, ref_id, memory_value, persistence, decay, consolidated |
| preneural_node_state | 2500 | node_state_id, recursive_run_id, iteration_n, clock_n, preneural_node_id, node_id, x, y, z, input_energy |
| topdown_feedback_signal | 2000 | feedback_id, recursive_run_id, iteration_n, clock_n, trajectory_id, target_preneural_node_id, feedback_gain, predicted_phase, prediction_error, correction_dx |
| transport_cost_matrix_record | 1800 | record_id, perturbation_run_id, base_run_id, window_from, window_to, source_uid, target_uid, geometry_cost, signal_cost, boundary_cost |
| information_relative_coordinate_snapshot | 1500 | info_coord_id, recursive_run_id, event_id, source_cell_uid, source_fiber_id, node_id, clock_n, channel_type, origin_ref, rel_x |
| raw_event_stream | 1500 | event_id, state_run_id, source_run_id, source_cell_uid, source_fiber_id, node_id, window_id, clock_n, x, y |


### `outputs/m34.db`

v34 Full base governance / proxy + external entropy control plane on cumulative base

| table | rows | columns |
| --- | --- | --- |
| v27_measure_field_cell | 13725 | field_cell_id, grid_id, measure_kind, time_bin, x_bin, y_bin, z_bin, source_sequence, source_frame, source_track_id |
| v27_measure_point_sample | 13725 | sample_id, point_id, transform_id, trajectory_trace_refs_json, measure_kind, measure_id_refs_json, field_cell_id, source_sequence, source_frame, source_track_id |
| full_replay_event_buffer_v03 | 13500 | replay_event_id, scenario_id, original_event_id, clock_n, original_node_id, replay_node_id, channel_type, original_value, replay_value, original_phase |
| v27_reversible_query_index | 11278 | query_index_id, query_key, query_kind, target_id, point_refs_json, transform_refs_json, trajectory_trace_refs_json, field_cell_refs_json, p_measure_refs_json, r |
| v32_adapter_output_mapping | 10418 | mapping_id, source_event_id, information_point_ref, trajectory_window_ref, measure_ref, shadow_ref, divergence_ref, intervention_ref, macro_ref, policy_ref |
| v32_general_source_event | 10418 | source_event_id, source_kind, adapter_id, source_ref_table, source_ref_id, event_role, event_time, x, y, z |
| preneural_edge_state | 5000 | edge_state_id, recursive_run_id, iteration_n, clock_n, source_preneural_node_id, target_preneural_node_id, spatial_distance, phase_lag, recurrent_weight, conduc |
| coordinate_transform_trace_v25 | 4575 | transform_id, source_point_id, from_coordinate_system, to_coordinate_system, raw_x, raw_y, raw_z, normalized_x, normalized_y, normalized_z |
| information_point_v25 | 4575 | point_id, source_id, source_dataset, source_sequence, source_frame, source_track_id, sample_id, sensor_id, sensor_kind, clock_domain |
| shadow_cell_sphere_mapping_v26 | 4575 | mapping_id, shadow_spacetime_cell_id, shadow_cell_id, source_point_id, legacy_cell_uid, cell_sphere_x, cell_sphere_y, cell_sphere_z, distance_to_legacy_cell, ma |


### `outputs/m35.db`

v35 Attention proposal + path-integral audit overlay

| table | rows | columns |
| --- | --- | --- |
| v35_attention_region_index | 160 | region_id, source_kind, source_ref, window_ref, support_domain, p_ref, r_ref, xi_ref, ledger_ref, read_only_semantic_label |
| v35_attention_tension_map | 160 | tension_id, region_id, p_mass, r_counter_mass, xi_residual_mass, anomaly_mass, persistence, boredom_decay, attention_tension, tension_rank |
| v35_attention_performance_report | 120 | report_id, proposal_id, path_integral_id, delta_F_attn, A_path, SNR_path, persistence_gain, Xi_change, verdict, recommended_next |
| v35_attention_proposal | 120 | proposal_id, proposal_type, target_region_ref, rationale_source, proposed_intensity, duration_budget_windows, proxy_provenance_id, sandbox_only, real_action_aut |
| v35_attentional_path_integral_audit | 120 | path_integral_id, proposal_id, path_type, path_definition_json, integrated_delta_F_ext, integrated_dissipation, integrated_anomaly_mass, mean_SNR_path, boundary |
| v35_r_counter_chain | 120 | r_chain_id, r_ref, region_id, counter_mass, persistence, closure_fraction, continuity_need, action_hint |
| v35_attention_transition_log | 119 | transition_id, from_proposal_id, to_proposal_id, trigger_source, window_span, transition_cost, ledger_budget_ref |
| v35_p_inertia_profile | 59 | p_inertia_id, p_ref, persistence, confirmed_overlap, anchor_drift, inertia_score, relative_stasis_support |
| v35_boundary_leakage_audit | 40 | leakage_id, region_id, boundary_ref, leakage_flux, entropy_closure_gap, p_anchor_ref, xi_ref, recommendation |
| v35_xi_momentum_chain | 32 | xi_chain_id, xi_ref, region_id, xi_mass, momentum_score, ledger_persistence, reentry_allowed_via, direct_to_p_allowed |


### `outputs/m35H.db`

v35H Hyperedge incidence sidecar

| table | rows | columns |
| --- | --- | --- |
| v35h_hyperedge_incidence | 855 | row_id, hyperedge_id, node_id, node_role, incidence_weight, coo_index, source_table, source_ref |
| v35h_hypernode_registry | 747 | node_id, node_type, source_ref, window_ref, measure_ref, carrier_kind, created_by, semantic_label_in_mainline |
| v35h_hyperedge_ledger_weight | 120 | hyperedge_id, delta_F_ext, dissipation_proxy, noise_budget, anomaly_mass, snr_path, noether_status, final_weight, ledger_decision |
| v35h_hyperedge_proposal | 120 | hyperedge_id, proposal_kind, source_attention_ref, window_span, proposal_status, external_ledger_ref, truth_claimed |
| v35h_acceptance_report | 12 | check_id, status, details |
| v35h_hyperedge_gc_report | 12 | gc_id, hyperedge_id, gc_decision, kept_digest_only, runtime_payload_deleted, reason, heat_bath_transfer |
| v35h_hyperedge_appeal_registry | 10 | appeal_id, hyperedge_id, appeal_reason, structural_snr, persistent_anomaly_mass, appeal_status |
| v35h_runtime_manifest | 3 | item_id, artifact_path, format, sha256, description |


### `outputs/m36.db`

v36 Dissipative source / information-energy metric proxy

| table | rows | columns |
| --- | --- | --- |
| v36_information_energy_metric_proxy | 160 | metric_id, source_id, from_ref, to_ref, window_ref, L_info_track, L_ledger, rho, mu_IE, provisional_metric_proxy |
| v36_metric_anchor_audit | 160 | anchor_audit_id, metric_id, raw_anchor_ref, anchor_drift, metric_drift, drift_ratio, status, recommendation |
| v36_curvature_proxy | 120 | curvature_id, region_ref, source_id, abs_delta_xin, r_counter_mass, masking_tension, entropy_closure_gap, anomaly_persistence, confirmed_p_inertia, K_proxy |
| v36_dissipative_source_registry | 80 | source_id, source_kind, source_ref, window_span, support_domain, ledger_ref, D_mean, D_var, F_ext_var, SNR_struct |
| v36_delta_xin_field | 64 | delta_xin_id, xin_ref, source_id, window_m, delta_xin_raw, noise_budget, delta_xin_clean, fallback_only, diagnostic_note |
| v36_singularity_candidate | 21 | singularity_id, curvature_id, region_ref, K_proxy, SNR_struct, anomaly_persistence, noise_explained, candidate_status, recommended_action |
| v36_topological_heat_bath | 17 | heat_bath_id, origin_ref, origin_kind, dissipated_mass, ledger_ref, transfer_reason, noether_balance_preserved, reversible_digest |
| v36_acceptance_report | 12 | check_id, status, details, blocking |
| v36_metric_guardrail_audit | 8 | guard_id, guard_name, status, details, blocking |
| v36_downgrade_contract | 7 | contract_id, original_concept, cannot_adopt_reason, downgraded_object, minimization_or_correction, forbidden_interpretation, status |


### `outputs/m361.db`

v36.1 Variational external ledger bridge

| table | rows | columns |
| --- | --- | --- |
| v361_action_scoring_report | 120 | report_id, path_id, total_action_proxy, stationarity_defect_total, xin_var_mass, score_rank, verdict, recommended_next |
| v361_candidate_path_inventory | 120 | path_id, source_kind, window_start, window_end, support_ref, top_k_rank, path_length_proxy, candidate_status |
| v361_delta_xin_fallback_snapshot | 120 | fallback_id, path_id, delta_xin_observed, fallback_role, used_as_main_definition, notes |
| v361_external_ledger_lagrangian_proxy | 120 | lagrangian_id, functional_id, path_id, metric_kinetic, dissipation_cost, noise_cost, anomaly_cost, noether_violation_cost, legal_source_credit, total_L_proxy |
| v361_stationarity_defect | 120 | defect_id, path_id, el_residual_proxy, ledger_balance_residual, constraint_violation, stationarity_defect_total, defect_class, requires_reentry |
| v361_variational_metric_state | 120 | state_id, path_id, mu_ie_prev, mu_ie_next, metric_update_proxy, step_size_eta, bounded_update, raw_coordinate_replaced |
| v361_xin_variational_defect | 120 | xin_var_id, path_id, xin_var_mass, el_residual_component, ledger_component, constraint_component, unresolved_anomaly_component, reentry_policy, direct_to_pr_all |
| v361_acceptance_report | 12 | check_id, status, details, blocking |
| v361_downgrade_contract | 8 | item_id, original_philosophy_math, cannot_directly_use_reason, downgraded_engineering_object, minimization_or_revision, forbidden_interpretation, suspended_item |
| v361_action_functional_registry | 4 | functional_id, functional_name, status, scope, mathematical_intent, engineering_downgrade, forbidden_interpretation, coefficient_count, meta_proxy_required |


### `outputs/m362.db`

v36.2 Variational action revision / Xin_var bridge

| table | rows | columns |
| --- | --- | --- |
| v362_action_comparison_report | 120 | report_id, path_id, best_functional_id, best_action_proxy, runner_up_action_proxy, action_margin, recommendation, promotion_allowed |
| v362_candidate_path_inventory | 120 | path_id, source_overlay, path_role, window_start, window_end, hyperedge_ref, p_anchor_ref, r_chain_ref, xin_carrier_ref, topk_rank |
| v362_delta_xin_fallback_snapshot | 120 | snapshot_id, path_id, delta_xin_observed, noise_budget, cleaned_delta_xin, fallback_reason, used_as_main_definition |
| v362_discrete_action_score | 120 | score_id, path_id, functional_id, metric_kinetic_proxy, dissipation_cost, noise_cost, anomaly_cost, r_counter_cost, xin_mass_cost, noether_violation_cost |
| v362_stationarity_defect_proxy | 120 | defect_id, path_id, functional_id, left_perturbation_score, current_score, right_perturbation_score, finite_variation_residual, stationarity_status, analytic_so |
| v362_xin_var_closure_defect | 120 | xin_var_id, path_id, xin_carrier_ref, el_residual_proxy, ledger_balance_residual, constraint_violation, unresolved_anomaly_mass, xin_var_total, direct_to_pr_all |
| v362_acceptance_report | 12 | check_id, check_name, status, detail |
| v362_meta_proxy_registry | 12 | meta_proxy_id, object_name, object_kind, value, calibration_status, replacement_condition, forbidden_interpretation |
| v362_downgrade_contract | 9 | contract_id, original_philosophy_math, cannot_directly_adopt_reason, downgraded_engineering_object, minimization_revision_mechanism, suspended_items, rejected_i |
| v362_action_functional_candidate_library | 5 | functional_id, functional_name, version, role, formula_proxy, coefficient_manifest_ref, allowed_scope, forbidden_interpretation, enabled |


### `outputs/m363.db`

v36.3 R spacetime band / Xin continuity bridge

| table | rows | columns |
| --- | --- | --- |
| v363_band_segment_link | 450 | link_id, band_id, seq, from_block, to_block, discontinuity_score, scale_switch_cost, kernel_switch_cost, ledger_dissipation_proxy, xin_residual_delta |
| v363_spacetime_block_registry | 180 | block_id, scale_level, window_start, window_end, kernel_radius, bandwidth, support_mass, envelope_ref, p_anchor_ref, ledger_ref |
| v363_pseudo_continuity_audit | 90 | audit_id, band_id, continuity_gain, smoothing_gain, structural_continuity_index, verdict, note |
| v363_r_spacetime_band_candidate | 90 | band_id, r_ref, p_anchor_ref, segment_count, scale_switch_count, continuity_cost, ledger_cost, xin_residual_after, pseudo_continuity_risk, status |
| v363_p_relative_stasis_profile | 60 | p_ref, support_scale, window_start, window_end, persistence_score, anchor_drift, p_stasis_score, downgrade_note |
| v363_xin_noncontinuity_ledger | 50 | xin_ref, source_band_ref, source_block_ref, noncontinuizable_score, ledger_presence_score, snr_struct, continuity_dilution_index, status, external_definition_re |
| v363_pde_like_continuity_residual | 40 | residual_id, target_ref, window_span, graph_laplacian_residual, boundary_flux_gap, ledger_closure_gap, pde_claimed, pde_like_proxy_only |
| v363_ledger_guided_smoothing_proposal | 24 | proposal_id, target_ref, proposal_kind, suggested_adjustment, expected_residual_reduction, sandbox_only, source_facts_rewritten, decision |
| v363_acceptance_report | 12 | check_id, status, detail |
| v363_downgrade_contract | 8 | concept, direct_risk, engineered_object, minimization_or_revision, forbidden_interpretation, suspended_item, rejected_item |


### `outputs/m364.db`

v36.4 Constrained coupler / R-band / Xin triage bridge

| table | rows | columns |
| --- | --- | --- |
| v364_dynamic_beam_state | 600 | beam_state_id, band_id, step_index, k_max, beta, cumulative_discontinuity, effective_beam_width, pruned_branch_count |
| v364_dissipation_light_cone | 240 | cone_id, source_block_ref, candidate_block_ref, ledger_budget, transition_cost, allowed, rejection_reason, source_facts_rewritten |
| v364_pseudo_continuity_score | 120 | pseudo_id, band_id, continuity_gain, smoothing_gain, structural_continuity_index, pseudo_continuity_risk, reason |
| v364_r_band_candidate_search | 120 | band_id, r_ref, anchor_id, beam_rank, segment_count, cumulative_discontinuity, scale_switch_count, kernel_switch_count, ledger_cost, within_p_tunnel |
| v364_variational_coupling_cost | 120 | cost_id, band_id, c_r_continuity, c_p_anchor, c_xin_residual, c_metric_distortion, c_ledger_violation, c_pseudo_smoothing, c_total, selected |
| v364_xin_triage_policy | 85 | xin_triage_id, xin_ref, band_id, triage_class, residual_mass, foreground_relevance, action_taken, ledger_ref, xin_direct_to_p_allowed, xin_direct_to_r_allowed |
| v364_p_anchor_tunnel_profile | 60 | anchor_id, p_ref, window_start, window_end, stasis_score, anchor_drift, tunnel_radius_proxy, markov_neighborhood_ref, semantic_label, source_facts_rewritten |
| v364_cognitive_field_residual_audit | 40 | audit_id, region_ref, window_id, k_proxy, metric_distortion, p_mass_proxy, r_pressure_proxy, xin_charge_proxy, field_residual_proxy, used_as_loss |
| v364_coupler_decision_report | 40 | decision_id, r_ref, selected_band_id, decision_class, total_cost, deferred_xin_count, heat_bath_transfer, appeal_count, summary |
| v364_acceptance_report | 12 | check_id, status, detail |


### `outputs/m365.db`

v36.5 Semantic stripping + Xin carrier + external readout overlay

| table | rows | columns |
| --- | --- | --- |
| v365_external_real_input_envelope_binding | 160 | envelope_ref, source_kind, source_event_ref, source_ref_table, source_ref_id, window_id, envelope_scope, continuous_field_assumption, real_input_desync_risk, ru |
| v365_external_semantic_readout_result | 31 | readout_id, external_module_id, readout_target_ref, target_table, readout_kind, classification_ref, readout_confidence, source_refs_json, ledger_refs_json, allo |
| v365_xin_minimal_carrier_state | 31 | xin_carrier_id, source_xi_ref, source_T_ref, source_O_ref, source_P_ref, source_R_ref, source_window_id, support_domain_ref, residual_mass_proxy, ledger_ref |
| v365_acceptance_report | 12 | check_id, status, details, blocking |
| v365_upper_recursion_semantic_null_contract | 9 | contract_id, layer_name, allowed_internal_fields_json, forbidden_internal_fields_json, external_readout_ref_allowed, semantic_backwrite_allowed, enforcement_sta |
| v365_external_xin_definition_ref | 6 | definition_ref, external_module_id, definition_family, allowed_output_kind, writes_mainline, confidence_policy, forbidden_interpretation |
| v365_semantic_contamination_audit | 5 | audit_id, audit_scope, target_ref, issue_type, issue_count, severity, action_taken, blocking, details |
| v365_downgrade_suspension_rejection_register | 4 | item_id, original_philosophy_math_claim, direct_use_risk, downgraded_engineering_object, minimization_or_revision_mechanism, suspended_items, rejected_items, fo |
| v365_external_module_registry | 4 | external_module_id, module_name, module_role, read_only, writes_mainline, allowed_outputs_json, governance_status, notes |
| v365_readout_backwrite_block_event | 4 | block_event_id, external_module_id, attempted_target_table, attempted_target_ref, attempted_write_kind, blocked, reason, created_at |


### `outputs/m365_full_rebase.db`

v36.5 full-lineage rebase manifest / coverage / boundary proof

| table | rows | columns |
| --- | --- | --- |
| rebase_acceptance_report | 48 | check_id, status, detail |
| rebase_version_coverage | 19 | version_id, active_dir, db_path, implementation_status, artifact_origin |
| rebase_artifact_identity | 9 | key, value |
| rebase_boundary_audit | 9 | audit_id, rule, status, evidence |
| rebase_component_inventory | 4 | component_id, artifact_type, source_artifact, applied_status, notes |


### `outputs/v366/m365_full_chain_materialized.db`

Full-chain materialized integration index

| table | rows | columns |
| --- | --- | --- |
| information_point_to_trajectory | 13941 | link_id, point_id, trajectory_trace_id, source_track_id, sequence_id, window_index, window_start_frame, window_end_frame, window_start_time, window_end_time |
| information_point_3d4d_backprojection | 4575 | point_id, transform_id, source_id, source_dataset, source_sequence, source_frame, source_track_id, t, raw_x, raw_y |
| source_to_information_point | 4575 | point_id, source_id, source_dataset, source_sequence, source_frame, source_track_id, time_s, raw_x, raw_y, raw_z |
| external_entropy_ledger_materialized | 4489 | entropy_event_id, source_ref_table, source_ref_id, window_id, event_kind, ledger_role, structure_potential, external_entropy, ext_free_energy_proxy, evidence_re |
| table_inventory | 1242 | db_alias, table_name, row_count, column_count, selected_for_materialization, materialization_role |
| hyperedge_incidence_materialized | 855 | row_id, hyperedge_id, node_id, node_role, incidence_weight, coo_index, source_table, source_ref, node_type, node_source_ref |
| counter_evidence_chain_materialized | 532 | r_measure_id, target_p_measure_id, trajectory_trace_id, source_track_id, counter_window_start_frame, counter_window_end_frame, counter_support_point_count, coun |
| pr_xin_to_external_ledger | 532 | link_id, p_measure_id, r_measure_id, xi_surface_id, trajectory_trace_id, evidence_bundle_id, p_external_ledger_ref, r_external_ledger_ref, xi_external_ledger_re |
| trajectory_to_o_pr_r_xin | 532 | trajectory_trace_id, source_track_id, window_start_frame, window_end_frame, o_candidate_id, p_measure_id, r_measure_id, xi_surface_id, p_status, r_status |
| spacetime_band_coupler_materialized | 210 | band_id, r_ref, p_anchor_ref, segment_count, continuity_cost, ledger_cost, xin_residual_after, pseudo_continuity_risk, band_status, coupler_decision_id |


### `outputs/v366/m366_process_window_pass3.db`

v36.6 process_window + hypernode spacetime backprojection

| table | rows | columns |
| --- | --- | --- |
| v366_process_window_member | 22128 | member_id, process_window_id, member_type, source_table, source_ref, role, version_ref, confidence_proxy, direct_fk_available, resolution_method |
| v366_hyperedge_spacetime_relation | 2625 | relation_id, hyperedge_id, node_a_ref, node_b_ref, backprojection_a_ref, backprojection_b_ref, delta_t, spatial_distance_proxy, same_trajectory_window, same_sup |
| preneural_process_window_member_pass2 | 2000 | member_id, process_window_id, member_type, source_table, source_ref, role, version_ref, confidence_proxy, direct_fk_available, resolution_method |
| process_window_materialization_confidence_pass3 | 1633 | process_window_id, window_kind, materialization_confidence_class, materialization_confidence_score, architecture_route_legitimacy, architecture_route_score, com |
| stage2_bypass_and_route_legitimacy_pass3 | 1633 | process_window_id, window_kind, direct_source_table, direct_source_ref, stage2_route_status, neural_substrate_status, architecture_route_legitimacy, legitimacy_ |
| v366_process_window_registry | 1633 | process_window_id, source_version_span, window_kind, time_start, time_end, support_domain_ref, information_payload_ref, operator_trace_ref, external_envelope_re |
| process_window_strengthening_pass2 | 1133 | process_window_id, window_kind, old_quality_class, old_quality_score, new_quality_class, new_quality_score, added_measure_binding, added_ledger_binding, added_b |
| v366_process_window_measure_binding | 893 | binding_id, process_window_id, p_measure_ref, r_measure_ref, xi_surface_ref, p_measure_value, r_measure_value, xi_residual_mass, counter_evidence_ref, masking_r |
| hypernode_fk_upgrade_applied_pass2 | 855 | applied_id, hypernode_id, hyperedge_id, node_role, node_type, old_node_source_ref, normalized_source_table, normalized_source_ref, target_exists, direct_fk_avai |
| v366_hypernode_spacetime_backprojection | 855 | backprojection_id, process_window_id, hypernode_id, hyperedge_id, source_table, source_ref, node_role, resolved_object_type, information_point_ref, trajectory_w |


### `outputs/v366/m366_implementation_coverage_audit.db`

Implementation coverage / maturity audit

| table | rows | columns |
| --- | --- | --- |
| evidence_strength_matrix | 56 | concept_id, concept, maturity_level, row_count, algorithmic_computation, native_run_generated, materialized_integration, directness_status, confidence |
| implementation_coverage | 56 | concept_id, version, concept, placement_class, intended_role, maturity_level, maturity_rank, evidence_db, evidence_table, row_count |
| implementation_gap_index | 39 | concept_id, version, concept, maturity_level, placement_class, current_limit, next_action, directness_status |
| maturity_scale | 7 | maturity_level, maturity_rank, definition |
| full_chain_realization_status | 6 | status_key, status_value, interpretation |
| acceptance_report | 5 | check_id, check_name, status, observed_value, required_value, notes |


### `outputs/v366/m366_upper_layer_empirical.db`

Upper-layer empirical analysis

| table | rows | columns |
| --- | --- | --- |
| empirical_evidence_bundle_traceability | 532 | bundle_id, trajectory_trace_id, p_measure_id, r_measure_id, xi_surface_id, source_point_count, coordinate_transform_count, masking_ref_count, ledger_ref_count,  |
| empirical_trajectory_toprxin_profile | 532 | trajectory_trace_id, source_track_id, sequence_id, window_index, window_start_frame, window_end_frame, sample_count, point_count, support_cell_count, path_lengt |
| empirical_track_role_sequence | 86 | track_id, window_count, role_sequence_json, p_mean, r_mean, xin_mean, interpretation |
| empirical_role_transition_counts | 24 | from_role, to_role, transition_count, representative_track, representative_from_window, representative_to_window |
| empirical_full_chain_backtrace_sample | 20 | sample_id, source_point_id, trajectory_trace_id, point_frame, source_track_id, p_measure_id, p_value, r_measure_id, r_value, xi_surface_id |
| empirical_variational_path_samples | 14 | path_id, path_role, hyperedge_ref, p_anchor_ref, r_chain_ref, xin_carrier_ref, total_action_proxy, stationarity_status, finite_variation_residual, xin_var_total |
| empirical_metric_distribution | 12 | metric_group, metric_name, n, min, q25, median, q75, max, mean, interpretation |
| empirical_information_transformation_pipeline | 11 | step_order, step_name, input_form, operation, output_form, empirical_tables, empirical_count, what_it_recognizes_or_separates |
| empirical_attention_recognition | 10 | bucket, label, count, share, interpretation |
| empirical_r_band_status_counts | 9 | source_table, status_or_class, count, interpretation |


### `outputs/v366/m366_build_pass12_execution.db`

Native-shaped skeleton + offline stress projection

| table | rows | columns |
| --- | --- | --- |
| pass12_native_skeleton_trace | 3724 | trace_id, run_id, stage_order, stage_name, trajectory_trace_id, source_track_id, input_ref, output_ref, process_window_ref, directness_class |
| pass12_stress_projection_result | 3192 | result_id, trajectory_trace_id, stress_id, stress_name, baseline_p_status, baseline_r_status, baseline_xi_status, projected_effect, projected_role, p_to_r_proje |
| pass12_sample_full_trace | 20 | sample_id, source_point_id, trajectory_trace_id, evidence_bundle_id, p_measure_id, r_measure_id, xi_surface_id, entropy_event_ref, attention_ref, hyperedge_id |
| pass12_upper_layer_effect_observation | 10 | observation_id, layer_name, recognizes, separates, information_change, evidence_table, evidence_count, limitation |
| pass12_run_manifest | 8 | key, value |
| pass12_acceptance_report | 7 | check_id, status, observed, requirement, note |
| pass12_execution_result_matrix | 6 | stress_id, stress_name, trajectory_windows, p_to_r_projected, r_or_p_to_xin_projected, stable_retained, boundary_blocked, interpretation |


### `outputs/v366/m366_build_pass13_native_replay.db`

Sample native-shaped replay / perturbation comparison

| table | rows | columns |
| --- | --- | --- |
| pass13_native_replay_stage_output | 5880 | row_id, run_id, sample_id, scenario_id, stage_order, stage_name, input_ref, output_ref, output_table, process_window_ref |
| pass13_attention_replay_output | 490 | attention_output_id, sample_id, scenario_id, attention_ref, baseline_verdict, scenario_verdict, intensity_proxy, recommended_next |
| pass13_baseline_vs_perturbation | 490 | comparison_id, sample_id, scenario_id, baseline_role, scenario_role, p_delta, r_delta, xin_delta, transition_class, evidence_strength |
| pass13_counter_masking_output | 490 | output_id, sample_id, scenario_id, r_measure_id, mask_ref, mask_behavior, r_chain_effect, boundary_blocked |
| pass13_hyper_variational_readout_output | 490 | output_id, sample_id, scenario_id, hyperedge_ref, variational_path_ref, action_proxy, stationarity_status, xin_var_proxy, xin_carrier_ref, readout_ref |
| pass13_ledger_replay_output | 490 | ledger_output_id, sample_id, scenario_id, ledger_ref, baseline_residual_proxy, scenario_residual_proxy, delta_residual_proxy, governance_verdict, source_facts_r |
| pass13_toprxin_replay_output | 490 | output_id, run_id, sample_id, scenario_id, trajectory_trace_id, p_value, r_value, xin_value, p_status, r_status |
| pass13_replay_sample_set | 70 | sample_id, sample_group, trajectory_trace_id, source_track_id, window_start_frame, window_end_frame, evidence_bundle_id, p_measure_id, r_measure_id, xi_surface_ |
| pass13_case_study_trace | 20 | case_id, sample_id, scenario_id, trajectory_trace_id, source_point_refs_json, stage_chain_json, baseline_vs_scenario_json, concise_interpretation |
| pass13_state_transition_summary | 14 | scenario_id, transition_class, count, pct |


## 10. 当前项目的主要问题 / 风险

1. **仍是 materialized integration，而非完整 native runtime**：很多结果来自已有 DB/sidecar/overlay 的整合，不是同一原生 run 从 source 到 readout 全量同步生成。
2. **上层到底层 direct FK 不完整**：hyperedge、variational path、Xin carrier 到 information point / trajectory 的很多连接仍是 inferred/proxy 或 normalized candidate。
3. **当前数据偏稳定**：强 R、强 Xin、强 novelty 场景主要来自压力投影或 native-shaped replay，不是大量真实扰动源重跑。
4. **Stage 2 合法绕过但需说明**：旧式 Stage 2 object surface 不是当前硬必经层；当前类神经主体更多由 T/O/P/R/Xin + storage + ledger + external modules 承担。
5. **外部模块是最小只读实现**：已有 external Xin definition/readout/backwrite blocker，但完整 taxonomy、capacity audit、PDE-like residual readout 仍未完成。
6. **行业化不足**：缺生产级权限、实时 agent tracing、云部署、API、UI、持续数据接入和模型评测闭环。

## 11. 对其他 AI 的阅读建议

如果你是另一个 AI，需要继续理解/开发这个项目，推荐按以下顺序阅读：

1. `m366_implementation_coverage_audit.db`：先看哪些理念已实现，哪些只是 blueprint。
2. `m366_upper_layer_empirical.db`：看项目当前到底识别/分离了什么。
3. `m365_full_chain_materialized.db`：看全链路物化数据。
4. `m366_process_window_pass3.db`：看 process_window 和 hypernode backprojection。
5. `m366_build_pass12_execution.db` 和 `m366_build_pass13_native_replay.db`：看压力投影与样本级重放。
6. `m25.db`：看底层 information point、coordinate transform、trajectory、P/R/Xin 的真实数据底座。

不要把以下内容误认为已经实现：真实 PDE、在线生命 runtime、真实物理度规、原生超图数据库、外部语义模块反写主线。

## 12. 总结

当前 Morphosphere 是一个研究型、白盒、可审计的信息时空轨迹系统。它最有价值的部分不是“预测准确率”，而是把信息从源头到 P/R/Xin、账本、attention、hyperedge、variational 和 readout 的全过程保存成可检查的数据关系。对行业而言，它可被视为 AI observability、data lineage、scientific data governance 与 agent traceability 的实验性融合原型。