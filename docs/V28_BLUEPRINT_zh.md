# Morphosphere v2.8 施工蓝图：Shadow-Evidence Divergence Gate

**版本定位**：v2.8 `shadow_evidence_divergence_gate`  
**目标**：让 v2.5 的 Evidence 面、v2.6 的 Shadow 面、v2.7 的可逆查询索引发生“碰撞”，计算 Shadow 与 Evidence 的散度，并把结果转化为更坚固的 P、可惩罚的 Shadow overreach、可进入 Xi 或 Emergence Alert 的 Evidence surprise。  
**交付性质**：施工蓝图，不是代码实现。  
**核心边界**：不 hot-swap、不改写 source facts、不让 Xi 顶替 P/R、不继续盲目堆新层。

---

## 0. 蓝图摘要

v2.8 的核心任务不是继续添加宏观概念，而是对已有结构进行第一次真正的“预测-证据审判”。

已有三块基础：

1. **v2.5 Evidence Reconstruction Store**：保存真实 CTC 信息点、坐标变换链、轨迹窗口、P/R/Xi 测度依据、calculation recipe 与 evidence bundle。
2. **v2.6 Shadow Cell-Sphere Reconstruction**：从真实 CTC 轨迹生成旁路 shadow cell-sphere、shadow motion state、shadow graph edge 与 shadow P/R/Xi comparison。
3. **v2.7 Measure Field + Reversible Query**：把信息点、轨迹、测度、坐标和查询索引物化，使单点、单轨迹、单窗口、单测度可逆向查询。

v2.8 要做的是：

```text
Evidence 面：真实发生的点、轨迹、测度、连接
Shadow 面：暗影底层预测的点、轨迹、测度、连接

二者按时间窗口、空间支撑域、轨迹、边、测度质量对齐比较。
```

结果分为五类：

```text
Shadow ∩ Evidence       -> confirmed P structure
Shadow - Evidence       -> shadow overreach / false positive / parameter penalty
Evidence - Shadow       -> evidence surprise / Xi residual / emergence candidate
Shadow ≈ Evidence + 偏移 -> calibration drift / R counterstructure
局部重合但拓扑不同      -> partial P + hidden R + masking required
```

---

## 1. 为什么 v2.8 必须先做散度，而不是继续建新层

项目目前已经从早期诊断账本走到真实数据接入：真实 CTC 源 ZIP 已被提取为 4575 个 centroid 信息点，形成真实时序轨迹，并被用于 v2.5 和 v2.6。

如果继续只建新层，会出现三个风险：

1. **Evidence 与 Shadow 分裂**：一套系统记录真实证据，另一套系统生成暗影预测，但二者不互相反证。
2. **P/R/Xi 重新退化成分数表**：没有 Shadow-Evidence 碰撞，P 仍可能只是 `p_score`，R 仍可能只是 `r_score`，Xi 仍可能只是 `xi_watch`。
3. **类神经结构失去原料可信度**：未来如果要把上层降级为审计层，真正的类神经 runtime 必须知道哪些预测被真实证据确认，哪些是幻觉，哪些是真实 surprise。

因此 v2.8 的原则是：

> 不再优先扩展系统，而是让已有系统互相审判。

---

## 2. v2.8 的核心定义

### 2.1 Evidence

Evidence 指真实数据驱动、可追踪、可反投的证据结构。它不是抽象标签，而是来自真实 CTC 源数据的时空点集、轨迹窗口和测度场。

主要来源：

```text
information_point_v25
coordinate_transform_trace_v25
trajectory_window_trace_v25
p_spacetime_measure_v25
r_counter_measure_v25
xi_residual_surface_v25
decision_evidence_bundle_v25
v27_measure_field_cell
v27_reversible_query_index
```

Evidence 的最小单位可以是：

```text
point-level evidence      -> 单个真实 centroid 信息点
window-level evidence     -> 跨窗口轨迹片段
edge-level evidence       -> 同窗口或相邻窗口中实际发生的时空邻接/连续关系
measure-level evidence    -> P/R/Xi 测度质量在 t,x,y,z 上的占据
```

### 2.2 Shadow

Shadow 指由真实数据驱动生成、但并非原始事实的旁路底层预测结构。它代表“如果让真实 CTC 轨迹塑造一个底层细胞球，它可能长成什么样”。

主要来源：

```text
shadow_cell_identity_v26
shadow_spacetime_cell_v26
shadow_cell_motion_state_v26
shadow_graph_edge_v26
shadow_pr_xi_comparison_v26
shadow_decision_evidence_bridge_v26
```

Shadow 的最小单位可以是：

```text
shadow-state             -> 某 track/frame 的暗影细胞状态
shadow-motion-window     -> 暗影跨窗口运动状态
shadow-edge              -> 暗影预测的邻接/连续/相似关系
shadow-measure           -> 暗影对 P/R/Xi 的预测或倾向
```

### 2.3 Divergence

Divergence 是 Evidence 与 Shadow 的差异测度。它不只是简单集合差，而是带权、带时间窗口、带空间支撑域、带轨迹关系、带拓扑关系的散度。

建议形式：

```text
D_shadow_evidence =
  w_edge       * edge_mismatch
+ w_traj       * trajectory_support_mismatch
+ w_measure    * occupancy_measure_mismatch
+ w_time       * temporal_lag
+ w_space      * spatial_offset
+ w_topology   * topology_difference
+ w_xi         * xi_surprise_mass
```

其中每一项都必须有 evidence refs 和 shadow refs，不能只存总分。

---

## 3. v2.8 的数据流

```text
v25 Evidence Store
  -> evidence_edge_extraction
  -> evidence_measure_support

v26 Shadow Reconstruction
  -> shadow_edge_extraction
  -> shadow_measure_support

v27 Reversible Query Index
  -> point / trajectory / measure / coordinate lookup

三者合流：
  -> shadow_evidence_alignment
  -> divergence decomposition
  -> confirmed P / shadow overreach / evidence surprise
  -> Xi residual update / emergence candidate
  -> replay and acceptance
```

施工时必须保证：

```text
source facts 不改写
shadow 不变成 source truth
evidence 不被 shadow 覆盖
Xi 不直接变 P/R
任何 confirmed P 都必须能反查到 Evidence + Shadow 的重合依据
```

---

## 4. v2.8 建议新增表

### 4.1 `v28_run_manifest`

记录本轮运行边界。

| 字段 | 类型 | 说明 |
|---|---|---|
| run_id | text | v2.8 run id |
| version | text | `shadow_evidence_divergence_gate_v2.8` |
| evidence_source_version | text | v2.5 / v2.7 |
| shadow_source_version | text | v2.6 |
| source_facts_rewritten | integer | 必须为 0 |
| hot_swap_allowed | integer | 必须为 0 |
| xi_direct_to_pr_allowed | integer | 必须为 0 |
| created_at | text | 运行时间 |

### 4.2 `v28_evidence_edge`

把 Evidence 里的真实轨迹/点集关系转成可比较的 edge。

| 字段 | 类型 | 说明 |
|---|---|---|
| evidence_edge_id | text | Evidence edge id |
| sequence_id | text | CTC sequence |
| window_id | text | 时空窗口 |
| frame_start | integer | 起始 frame |
| frame_end | integer | 结束 frame |
| source_track_id | text | 真实 track |
| point_a_id | text | 起点信息点 |
| point_b_id | text | 终点信息点 |
| cell_a_ref | text | 映射细胞/支撑域 A |
| cell_b_ref | text | 映射细胞/支撑域 B |
| t_mid | real | 中点时间 |
| x_mid, y_mid, z_mid | real | 中点坐标 |
| edge_length | real | 4D/3D 轨迹局部长度 |
| continuity_mass | real | 连续性质量 |
| measure_mass | real | Evidence 测度质量 |
| evidence_bundle_ref | text | v25 bundle |

### 4.3 `v28_shadow_edge`

把 Shadow 预测连接转成相同规范的 edge。

| 字段 | 类型 | 说明 |
|---|---|---|
| shadow_edge_id | text | Shadow edge id |
| shadow_cell_a | text | 暗影节点 A |
| shadow_cell_b | text | 暗影节点 B |
| window_id | text | 时空窗口 |
| predicted_t_mid | real | 预测时间 |
| predicted_x_mid, predicted_y_mid, predicted_z_mid | real | 预测坐标 |
| predicted_length | real | 预测边长度 |
| predicted_continuity | real | 预测连续性 |
| predicted_measure_mass | real | 暗影测度质量 |
| shadow_motion_state_ref | text | v26 motion ref |
| shadow_bridge_ref | text | v26 evidence bridge ref |

### 4.4 `v28_shadow_evidence_alignment`

记录 Evidence edge 与 Shadow edge 的匹配关系。

| 字段 | 类型 | 说明 |
|---|---|---|
| alignment_id | text | alignment id |
| evidence_edge_id | text | Evidence edge |
| shadow_edge_id | text | Shadow edge |
| window_id | text | 对齐窗口 |
| temporal_delta | real | 时间差 |
| spatial_delta | real | 空间差 |
| length_delta | real | 长度差 |
| measure_overlap | real | 测度重合质量 |
| topology_match | real | 拓扑匹配度 |
| alignment_status | text | matched / shifted / partial / unmatched |
| alignment_confidence | real | 对齐置信度 |

### 4.5 `v28_divergence_decomposition`

记录散度分解，而不是只存总分。

| 字段 | 类型 | 说明 |
|---|---|---|
| divergence_id | text | divergence id |
| window_id | text | 窗口 |
| support_domain_ref | text | 支撑域 |
| edge_mismatch | real | 边差异 |
| trajectory_support_mismatch | real | 轨迹支撑差异 |
| occupancy_measure_mismatch | real | 测度占据差异 |
| temporal_lag | real | 时间滞后 |
| spatial_offset | real | 空间偏移 |
| topology_difference | real | 拓扑差异 |
| xi_surprise_mass | real | Xi surprise 质量 |
| total_divergence | real | 加权总散度 |
| recipe_id | text | 计算 recipe |

### 4.6 `v28_confirmed_p_structure`

Shadow 与 Evidence 重合后确认出的更坚固 P。

| 字段 | 类型 | 说明 |
|---|---|---|
| confirmed_p_id | text | confirmed P id |
| parent_p_measure_ref | text | v25 P measure |
| shadow_support_ref | text | v26 shadow ref |
| alignment_ref | text | v28 alignment |
| window_span | text | 窗口跨度 |
| support_length_overlap | real | 长度重合 |
| support_duration_overlap | real | 时间重合 |
| support_domain_overlap | real | 支撑域重合 |
| equivalent_probability_boost | real | 等效概率提升 |
| free_energy_delta_proxy | real | 自由能 proxy 下降 |
| attention_yield_delta | real | 注意力让渡变化 |
| status | text | confirmed / strong / durable |

### 4.7 `v28_shadow_overreach_penalty`

Shadow 有但 Evidence 没有的预测过度。

| 字段 | 类型 | 说明 |
|---|---|---|
| penalty_id | text | penalty id |
| shadow_edge_id | text | 未被证实的 shadow edge |
| window_id | text | 窗口 |
| predicted_mass | real | 预测质量 |
| observed_mass | real | 真实证据质量，通常低或 0 |
| overreach_mass | real | 过度预测质量 |
| penalty_type | text | false_positive / topology_overreach / temporal_overreach |
| parameter_penalty_hint | text | 建议惩罚的参数/机制 |
| send_to_r | integer | 是否转入 R 审查 |
| send_to_xi | integer | 是否进入 Xi 暂存 |

### 4.8 `v28_evidence_surprise_xi`

Evidence 有但 Shadow 没有的 surprise。

| 字段 | 类型 | 说明 |
|---|---|---|
| surprise_id | text | surprise id |
| evidence_edge_id | text | 未被预测的 evidence edge |
| window_id | text | 窗口 |
| surprise_mass | real | surprise 质量 |
| persistence_across_windows | real | 跨窗口持续性 |
| xi_surface_ref | text | Xi residual surface ref |
| emergence_candidate | integer | 是否触发 emergence candidate |
| proto_o_candidate_allowed | integer | 是否允许经 O re-entry |
| reentry_policy | text | 必须为 via_o_candidate_only |

### 4.9 `v28_emergence_alert_candidate`

如果 Evidence surprise 跨窗口稳定，记录为 emergence candidate。

| 字段 | 类型 | 说明 |
|---|---|---|
| alert_id | text | alert id |
| surprise_refs | text/json | 相关 surprise |
| window_span | text | 跨窗口范围 |
| support_domain | text | 支撑域 |
| persistence_score | real | 持续性 |
| novelty_score | real | 新异性 |
| entropy_closure_status | text | 外部账本状态 |
| recommended_next_action | text | masking / replay / proto-O |

### 4.10 `v28_acceptance_report`

验收表。

| 字段 | 类型 | 说明 |
|---|---|---|
| check_id | text | 检查项 |
| status | text | PASS / FAIL |
| details | text | 说明 |

---

## 5. Runtime sidecar 设计

SQLite 不应存所有对齐矩阵和场值。v2.8 应继续遵守 runtime / ledger split。

建议新增：

```text
runtime_store/v28/
  evidence_edges_v28.jsonl
  shadow_edges_v28.jsonl
  alignment_v28.jsonl
  divergence_decomposition_v28.jsonl
  confirmed_p_structure_v28.jsonl
  shadow_overreach_penalty_v28.jsonl
  evidence_surprise_xi_v28.jsonl
  emergence_alert_candidate_v28.jsonl
```

SQLite 只保存：

```text
索引、摘要、行数、SHA256、recipe、acceptance、source digest
```

这样 v2.8 仍然可审计，但不会重新让 SQLite 成为运行时心脏。

---

## 6. 核心算法流程

### 6.1 归一化 Evidence Edge

从 v25 / v27 中读取真实轨迹窗口和点集，生成 Evidence Edge。

伪流程：

```text
for each trajectory_window_trace:
    points = source_point_refs ordered by frame
    for consecutive point pairs:
        build evidence_edge
        compute edge_length, continuity_mass, measure_mass
        store support cell refs and coordinate refs
```

### 6.2 归一化 Shadow Edge

从 v26 中读取 shadow graph 和 motion state，生成 Shadow Edge。

```text
for each shadow_graph_edge:
    find linked shadow_motion_state
    map to window_id and support domain
    compute predicted_length, predicted_continuity, predicted_measure_mass
```

### 6.3 对齐 Evidence 与 Shadow

对同一窗口、同一或邻近支撑域中的边进行匹配。

匹配标准建议：

```text
temporal_delta <= time_tolerance
spatial_delta <= spatial_tolerance
support_domain_overlap >= domain_threshold
```

匹配结果：

```text
matched    -> 高重合
shifted    -> 有证据但时间/空间偏移
partial    -> 局部重合
unmatched  -> 只有一边存在
```

### 6.4 计算散度

对每个窗口和支撑域，计算分解项：

```text
edge_mismatch = unmatched_edges / total_edges
trajectory_support_mismatch = 1 - support_domain_overlap
occupancy_measure_mismatch = abs(evidence_mass - shadow_mass)
temporal_lag = mean temporal_delta
spatial_offset = mean spatial_delta
topology_difference = graph edit proxy
xi_surprise_mass = mass(Evidence - Shadow)
```

总散度：

```text
total_divergence = Σ w_i * component_i
```

### 6.5 生成三类主要结果

```text
matched high overlap
  -> confirmed P

shadow unmatched
  -> shadow overreach penalty

evidence unmatched
  -> evidence surprise Xi
```

### 6.6 触发 Emergence Alert

如果 Evidence surprise 满足：

```text
persistence_across_windows >= threshold
support_domain_stability >= threshold
not explained by known R
not numerical artifact
```

则触发：

```text
emergence_alert_candidate
```

但必须保持：

```text
Xi -> proto-O -> O -> P/R
```

不能直接：

```text
Xi -> P/R
```

---

## 7. P/R/Xi 在 v2.8 中的重新落实

### 7.1 P_k

v2.8 中更坚固的 P 不再只是 v25 的 P measure，而是：

```text
P_k_confirmed = P_evidence ∩ P_shadow
```

或者更准确：

```text
P_k_confirmed = overlap(Evidence_measure, Shadow_prediction, window, support_domain)
```

它应保存：

```text
support_length_overlap
support_duration_overlap
support_domain_overlap
equivalent_probability_boost
free_energy_delta_proxy
attention_yield_delta
```

### 7.2 R_k

R 在 v2.8 中主要来自三类：

```text
1. Shadow 与 Evidence 都存在但几何/相位/拓扑偏移
2. Shadow overreach 系统性竞争 Evidence
3. confirmed P 被 masking 后暴露出隐藏反结构
```

v2.8 不应该把 R 和 Xi 混淆。

### 7.3 Xi_k

Xi 在 v2.8 中主要接收：

```text
Evidence surprise
原因不明的 Shadow overreach
无法闭合的熵账本差异
未能归入 P/R 的 partial topology conflict
```

Xi 的原则继续保持：

```text
Xi 不能直接成为 P/R。
Xi 只能通过 proto-O / O candidate re-entry。
```

---

## 8. Calculation Recipe 要求

v2.8 必须记录至少以下 recipe：

```text
edge_extraction_from_evidence_v1
edge_extraction_from_shadow_v1
shadow_evidence_alignment_v1
divergence_decomposition_v1
confirmed_p_overlap_v1
shadow_overreach_penalty_v1
evidence_surprise_xi_v1
emergence_alert_candidate_v1
```

每个 recipe 必须记录：

```text
recipe_id
formula_text
input_refs
parameters_json
thresholds_json
code_path
code_hash
output_refs
```

---

## 9. 验收标准

v2.8 不以“数值漂亮”为通过标准，而以“散度链路真实可追踪”为通过标准。

必须通过：

```text
1. Evidence edge count > 0
2. Shadow edge count > 0
3. Alignment rows > 0
4. confirmed P rows > 0
5. shadow overreach rows > 0 或明确为 0 且有解释
6. evidence surprise rows > 0 或明确为 0 且有解释
7. 每个 confirmed P 可追溯到 evidence refs + shadow refs
8. 每个 surprise 可追溯到 evidence edge
9. 每个 overreach 可追溯到 shadow edge
10. Xi reentry policy = via_o_candidate_only
11. source_facts_rewritten = 0
12. hot_swap_allowed = 0
13. P/R before Xi preserved
14. SQLite quick_check = ok
15. runtime sidecar manifest sha256 可验证
```

建议增加反例测试：

```text
shifted_shadow_control: 人工平移 shadow 坐标，散度应上升
missing_evidence_control: 删除部分 evidence edge，overreach 应上升
missing_shadow_control: 删除部分 shadow edge，surprise/Xi 应上升
perfect_identity_control: 用 evidence 复制 shadow，confirmed P 应上升，散度应下降
```

---

## 10. 输出报告结构

v2.8 报告应包括：

```text
1. 运行摘要
2. Evidence 输入摘要
3. Shadow 输入摘要
4. Alignment 结果
5. Divergence 分解
6. Confirmed P 结构
7. Shadow Overreach 惩罚
8. Evidence Surprise / Xi
9. Emergence Candidate
10. Acceptance
11. 诚实边界
12. 下一步建议
```

---

## 11. 文件包策略

因为 v2.5 / v2.6 大包下载失败，v2.8 必须从设计上避免大包。

建议输出：

```text
m28.zip              # <= 10 MB，短名，工程核心
m28_db.zip           # <= 10 MB，DB 单独压缩
m28_manifest.json    # 极小
m28_blueprint.md     # 本蓝图
m28_report.md        # 运行报告
```

不得包含：

```text
Fluo-N2DH-GOWT1.zip
历史 full package
历史大 runtime store
重复 raw source archive
```

必须包含：

```text
outputs/m28.db
scripts/run_v28.py
scripts/accept_v28.py
scripts/query_v28.py
runtime_store/v28/*.jsonl
README.md
run.sh
```

---

## 12. v2.8 完成后的项目状态

v2.8 完成后，项目将从：

```text
Evidence 面已建立
Shadow 面已建立
可逆查询已建立
```

推进到：

```text
Evidence 与 Shadow 已碰撞
预测成功变成 confirmed P
暗影过度变成 penalty
真实 surprise 进入 Xi / Emergence
P/R/Xi 不再只是分数，而是来自预测-证据散度的时空测度结果
```

这一步是未来类神经 runtime 的关键原料，因为它告诉系统：

```text
哪些连接是真实验证过的
哪些连接是暗影幻觉
哪些连接是真实 surprise
哪些残余值得重新进入 O-candidate
```

---

## 13. 一句话结论

v2.8 应该是 Morphosphere 的第一次真正“预测-证据散度审判”。

它不应再继续堆层，而应让 v2.5 Evidence、v2.6 Shadow、v2.7 reversible query 三者相撞：

```text
重合 -> 坚固 P
Shadow 多出 -> 惩罚与 R/Xi 审查
Evidence 多出 -> Xi surprise / Emergence Alert
偏移 -> calibration drift / R counterstructure
```

这会把项目从“可追踪记录系统”推进到“可反证预测系统”。
