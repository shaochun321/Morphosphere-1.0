# Morphosphere v36.5 落地所需数理细节与工程问题矩阵

版本定位：`v36.5 semantic-stripped recursion + external semantic/readout + Xin carrier + real-input envelope`

交付性质：落地跟踪蓝图 / 不是代码实现 / 不是最终理论定稿

核心原则：主线内部不显式定义语义。主线只生成与保存轨迹、支撑域、测度、残余、账本引用、外部输入包裹引用、re-entry policy。语义、Xin 类型学、外部泄露判断、PDE ghost 判断、系统容量不足判断，应由外部模块从存储系统与外部账本中后验读出。

---

## 0. 总体判断

落地难度很高，但可以分层实施。

最小可运行版不应试图一次性实现真实连续场、完整外部世界同步、PDE 求解器、真正语义理解模块或类神经 runtime。第一版最重要的是建立边界：主线去语义化、Xin 最小承载、外部语义读出只读、真实输入包裹引用、语义污染审计与反写阻断。

推荐最小落地目标：

```text
主线内部：
  T / O / P / R / Xin / metric / attention / hyperedge
  不持有显式语义标签。

外部模块：
  从 SQLite / runtime_store / external ledger / source envelope / carrier states
  后验读出语义、Xin 分类和风险建议。

主线只接受：
  readout_ref
  classification_ref
  risk_level
  reentry_suggestion
  audit_status

主线禁止接受：
  truth label
  final object meaning
  real physical claim
  direct semantic overwrite
```

---

## 1. 必须落地的数理对象

### 1.1 外部真实输入连续场包裹层

哲学—数学意图：内部递归链虽然被工程实现为窗口、事件、轨迹、超边、账本行，但其数据总集应被一个更高层的外部真实输入连续场包裹。内部递归不能忘记自己不是外部真实时空本体。

工程对象：`external_real_input_envelope`

最小字段：

```text
envelope_id
source_stream_ref
source_time_span
source_spatial_or_support_span
sampling_policy
window_projection_refs
continuity_assumption_level
real_input_desync_risk
created_at
```

数理作用：

```text
E_real 不是内部对象，
而是所有 T/O/P/R/Xin carrier 的外部包裹引用。

每条内部轨迹 Γ_internal 必须满足：
  envelope_ref(Γ_internal) != NULL
```

可计算检查：

```text
coverage_ratio = count(objects with envelope_ref) / count(all mainline objects)
desync_score = f(replay_flag, sandbox_flag, shadow_flag, source_time_gap, adapter_delay)
```

---

### 1.2 时空测度代理

哲学—数学意图：已定义坐标系、带宽、核范围、跨窗口 transport / stitching，已经构成离散时空测度。它既支撑“长度”，也支撑路径概率。

工程对象：`spacetime_measure_proxy`

核心分量：

```text
coordinate_distance
kernel_support_overlap
bandwidth_cost
window_jump_cost
transport_cost
stitching_residual
support_boundary_cost
```

路径长度代理：

```text
L_ST(Γ) = Σ_m cost_ST(z_m, z_{m+1})
```

禁止解释：

```text
L_ST ≠ physical distance
L_ST ≠ true spacetime interval
```

---

### 1.3 信息—能量测度代理

哲学—数学意图：外部熵账本中的 ledger energy / effective energy / free-energy-like quantity 与信息时空轨迹共同诱导路径代价。

工程对象：`information_energy_metric_proxy`

候选形式：

```text
μ_IE(a,b,m) =
  ρ · L_info_track(a,b,m)
+ (1 - ρ) · L_ledger(a,b,m)
```

其中：

```text
L_info_track:
  基于轨迹长度、transport、kernel、bandwidth、support 连续性的内部路径代价。

L_ledger:
  基于外部账本 D/N/A/W/Noether-style closure 的代价。
```

路径作用量代理：

```text
S_IE[Γ] = Σ_m L_IE(z_m, z_{m+1}; θ)
```

路径概率代理：

```text
P(Γ) = exp(-S_IE[Γ] / β) / Z
```

禁止解释：

```text
μ_IE ≠ true physical metric
S_IE ≠ true physical action
P(Γ) ≠ true physical probability
```

---

### 1.4 Xin 最小承载状态

哲学—数学意图：项目内部不定义 Xin 的显式语义，只保存不可删除残余的承载、引用、测度和 re-entry policy。Xin 的类型学由外部模块定义。

工程对象：`xin_minimal_carrier_state`

最小字段：

```text
xin_carrier_id
source_T_refs
source_O_refs
source_P_refs
source_R_refs
source_event_refs
envelope_ref
window_span
support_domain_ref
residual_mass_proxy
ledger_ref
continuity_status
algebra_geometry_decoupling_score
foreground_status
reentry_policy
external_definition_ref
attention_priority
created_at
```

禁止字段：

```text
semantic_label
meaning
true_type
physical_cause
biological_label
final_explanation
```

---

### 1.5 外部 Xin 定义模块

哲学—数学意图：`外部泄露 / 容量不足 / PDE ghost / 对称性破缺 / 连续性破缺` 是解释，不是主线本体。它们应由外部模块基于存储系统和外部账本后验判定。

工程对象：`external_xin_definition_module`

输入：

```text
xin_minimal_carrier_state
external_entropy_ledger
spacetime_measure_proxy
information_energy_metric_proxy
source envelope
runtime_store support traces
```

输出：

```text
external_definition_ref
classification_candidate
confidence
risk_level
reentry_suggestion
external_module_request
forbidden_interpretation
```

主线只保存 `external_definition_ref`，不得复制语义正文。

---

### 1.6 主时空信息轨迹与 Xin 调度

哲学—数学意图：P/R/O 构造都会伴生 Xin，系统不能追逐所有 Xin。必须围绕当前主时空信息轨迹处理前台 Xin，其余挂账、热浴化或外部模块化。

工程对象：

```text
principal_trajectory_proxy
xin_triage_policy
foreground_xin_set
background_xin_set
deferred_xin_ledger
thermalized_xin_ledger
external_leakage_xin_queue
```

主长度代理：

```text
L_main(Γ) =
  λ_ST · L_spacetime(Γ)
+ λ_IE · L_information_energy(Γ)
+ λ_R  · R_continuity_cost(Γ)
+ λ_X  · active_Xin_cost(Γ)
+ λ_L  · ledger_violation_cost(Γ)
```

核心调度原则：

```text
minimize action-relevant Xin
while accounting for all remaining Xin
```

---

### 1.7 R 时空带与受约束变分耦合

哲学—数学意图：R 不是简单反例，而是为了获得连续性而构造跨尺度时空带。该构造不能全局搜索，必须受 P 锚点、外部账本、带宽、核范围、Xin budget 限制。

工程对象：

```text
r_spacetime_band_candidate
p_stasis_anchor_proxy
r_band_segment_link
pseudo_continuity_audit
constrained_variational_coupler
```

候选代价：

```text
C_total(B_R) =
  λ_R · C_R_continuity(B_R)
+ λ_P · C_P_anchor(B_R)
+ λ_X · C_Xin_residual(B_R)
+ λ_μ · C_metric_distortion(B_R)
+ λ_L · C_ledger_violation(B_R)
+ λ_s · C_pseudo_smoothing(B_R)
```

搜索约束：

```text
B_R ∈ Beam_K(candidate_blocks)
subject to:
  dissipation_light_cone
  P_island_tunnel
  ledger_budget
  kernel_bandwidth_limit
  max_scale_switch
  Xin_recursion_budget
```

---

### 1.8 外部语义读出函数

哲学—数学意图：语义不属于主线递归系统。语义应由外部 readout 模块从存储与账本中后验读出。

工程对象：

```text
external_semantic_readout_result
semantic_readout_module
semantic_contamination_audit
readout_backwrite_block_event
```

读出函数：

```text
Readout_sem:
  Store × Ledger × RuntimeTrace × Envelope
  -> ReadoutHypothesis
```

输出必须只读：

```text
readout_id
scope
source_refs
ledger_refs
confidence
hypothesis_text_or_code
forbidden_backwrite = 1
```

禁止：

```text
Readout_sem -> P/R/Xin direct write
Readout_sem -> metric scoring
Readout_sem -> action authorization
```

---

## 2. 必须建立的工程表 / 文件 / 模块

### 2.1 SQLite 表建议

```text
v365_semantic_null_contract
v365_external_real_input_envelope
v365_envelope_binding
v365_xin_minimal_carrier_state
v365_external_xin_definition_ref
v365_external_semantic_readout_result
v365_semantic_contamination_audit
v365_readout_backwrite_block_event
v365_principal_trajectory_proxy
v365_xin_triage_policy
v365_deferred_xin_ledger
v365_thermalized_xin_ledger
v365_real_input_desync_audit
```

### 2.2 runtime_store 目录建议

```text
runtime_store/v365/
  semantic_null_scan.jsonl
  xin_carrier_events.jsonl
  external_readout_results.jsonl
  backwrite_block_events.jsonl
  envelope_binding_audit.jsonl
  real_input_desync_audit.jsonl
  xin_triage_events.jsonl
  principal_trajectory_candidates.jsonl
```

### 2.3 代码模块建议

```text
active/v365/scripts/
  check_v365.py
  scan_semantic_contamination.py
  build_xin_minimal_carriers.py
  bind_external_input_envelopes.py
  run_external_semantic_readout.py
  block_readout_backwrite.py
  triage_xin_against_principal_trajectory.py
  audit_real_input_desync.py
  query_v365.py
```

---

## 3. 工程难点清单

### 3.1 旧表迁移与语义字段剥离

问题：历史版本中可能存在 `semantic_label / meaning / behavior_type / object_name / class_name` 之类显式语义字段或报告字段。

风险：如果直接删除，会破坏历史可读性；如果保留在主线，会污染去语义化原则。

策略：

```text
旧语义字段不直接删除。
先迁移到 external_readout_archive 或 report-only table。
主线对象只保留 readout_ref。
```

验收：

```text
mainline_semantic_label_count = 0
external_readout_archive_count >= previous_semantic_fields_count
```

---

### 3.2 外部模块反写阻断

问题：外部语义读出模块必须只读，但实际工程中很容易把 readout 结果用于 scoring、attention、metric 或 P/R 更新。

风险：语义重新夺权。

策略：

```text
所有 readout 输出进入 readout_result 表。
主线只允许引用 readout_id。
禁止主线使用 readout_text / semantic_label 作为条件。
运行时扫描 SQL / Python 调用路径。
```

验收：

```text
readout_backwrite_block_event records all attempted writes
semantic_readout_used_as_truth = 0
```

---

### 3.3 Envelope 引用的全链路覆盖

问题：每个 T/O/P/R/Xin/trajectory/hyperedge 对象都应绑定外部真实输入包裹引用，但历史对象可能没有该引用。

风险：内部轨迹看似自足，忘记外部真实输入支撑。

策略：

```text
先做 weak envelope binding：source file / source stream / window span。
再做 strong envelope binding：连续输入场 / adapter / source clock。
```

验收：

```text
envelope_coverage_ratio >= threshold
missing_envelope_objects reported but not silently ignored
```

---

### 3.4 Xin carrier 爆炸

问题：P/R/O 构造都会产生 Xin，如果每个残余都持久化为完整对象，会导致存储爆炸。

策略：

```text
foreground_xin: 完整 carrier
background_xin: summary carrier
deferred_xin: ledger ref + digest
thermalized_xin: heat bath balance only
external_leakage_xin: external module queue
```

验收：

```text
foreground_xin_count bounded
unbounded_xin_mass forbidden
xin_heat_bath_balance closed
```

---

### 3.5 R-band 组合爆炸

问题：R 为寻找连续性可能在多尺度、多窗口、多 kernel 范围中爆炸式拼接。

策略：

```text
1. dissipation_light_cone
2. P_island_tunnel
3. ledger_decayed_beam_search
4. max_scale_switch
5. max_window_jump
6. top-k candidate cap
```

验收：

```text
r_band_search_complexity <= configured_budget
beam_width_decays_with_discontinuity = true
```

---

### 3.6 伪连续性识别

问题：R-band 可能只是靠 kernel / bandwidth 扩大被强行平滑出来，并非真实结构连续。

指标：

```text
Continuity_Gain = Xin_before - Xin_after
Smoothing_Gain = residual_reduction_due_to_kernel_or_bandwidth_expansion
Structural_Continuity_Index = Continuity_Gain - η · Smoothing_Gain
```

验收：

```text
pseudo_continuity_risk flagged when smoothing_gain dominates
```

---

### 3.7 外部账本与主线权限边界

问题：外部账本可以约束、审计、建议，但不能直接写 P/R/Xin 主链。

策略：

```text
ledger_guided_smoothing_proposal is sandbox-only
ledger can emit risk/block/retry/heat_bath request
ledger cannot mutate source facts or P/R/Xin mainline
```

验收：

```text
external_ledger_can_write_mainline = 0
ledger_suggestion_has_audit_ref = 1
```

---

### 3.8 系数与阈值校准

问题：所有 λ、ρ、β、η、threshold、budget 都是 meta-proxy，不能被当作自然常数。

策略：

```text
v341_meta_proxy_registry 注册所有参数。
每个参数必须有 source、calibration_status、allowed_run_type、replacement_condition。
```

验收：

```text
unregistered_coefficient_count = 0
```

---

### 3.9 存储系统一致性

问题：SQLite、runtime_store、外部模块输出、sidecar hash 必须一致。

策略：

```text
manifest + sha256
runtime sidecar digest
ledger row count audit
rebuild_from_ledger script
```

验收：

```text
manifest_consistency_pass = 1
runtime_store_digest_match = 1
```

---

### 3.10 测试难点

必须测试：

```text
语义字段污染测试
外部 readout 反写测试
Xin carrier 生成测试
Envelope 缺失测试
R-band 组合爆炸测试
伪连续性测试
热浴守恒测试
meta-proxy 未登记测试
external module classification only-ref 测试
```

---

## 4. 原哲学—数学构想降级 / 悬置 / 否决矩阵

| 原哲学—数学构想 | 不能直接采用的原因 | 降级后的工程对象 | 最小化 / 修正机制 | 悬置项 | 否决项 |
|---|---|---|---|---|---|
| 上层递归无显式语义 | 旧代码和报告可能已有语义字段 | `semantic_null_contract` | 扫描、迁移、只读 readout | 完整历史语义迁移 | 主线继续写 semantic_label |
| 外部真实输入连续场 | 当前没有真实物理同步 runtime | `external_input_envelope_ref` | 弱绑定 source/window，逐步强绑定 | 完整连续场建模 | 内部轨迹无 envelope_ref 却自称完整 |
| Xin 由外部模块定义 | 主线不能证明 Xin 本体 | `xin_minimal_carrier` + `external_definition_ref` | 主线只保存 carrier 和 ref | 完整 Xin 类型学 | 主线写死 Xin 类型 |
| 语义由外部模块后验读取 | 外部模块也可能越权 | `external_readout_result` | 只读、禁止反写 | 真正语义理解模块 | readout 结果作为 truth |
| P/R/O 构造伴生 Xin | 可能导致无限残余 | `xin_triage_policy` | 前台、后台、延迟、热浴 | 完整 Xin 自我递归模型 | 追逐所有 Xin |
| R 构造连续时空带 | 全局搜索组合爆炸 | `r_band_candidate` | 光锥、P 隧道、动态束搜索 | 全局最优路径 | 无约束全局搜索 |
| 信息—能量测度定义路径概率 | 不是严格物理概率 | `path_probability_proxy` | softmax/top-k scoring | 连续概率流形 | 概率当真实物理概率 |
| 外部账本调节 Xin | 账本不能改写主链 | `ledger_guided_proposal` | sandbox-only | 完整动力学耦合 | 账本直接写 P/R/Xin |
| PDE ghost / external leakage | 无法证明真实 PDE | `external_module_request` | 外部模块候选，不写主线 | 真实 solver 集成 | 主线声明发现 PDE |
| 类神经 runtime | 当前不是这一阶段 | `future_runtime_placeholder` | 只保留接口 | v37+ runtime | v36.5 同时重写 runtime |

---

## 5. 建议实施阶段

### Phase 0：审计，不改写

```text
scan_semantic_contamination.py
scan_missing_envelope_refs.py
scan_xin_semantic_fields.py
```

交付：污染报告、缺失 envelope 报告、旧语义字段清单。

### Phase 1：最小 schema 加壳

```text
v365_semantic_null_contract
v365_xin_minimal_carrier_state
v365_external_semantic_readout_result
v365_readout_backwrite_block_event
```

交付：可运行 DB 增量，不改历史主线内容。

### Phase 2：外部 readout 只读模块

```text
external_readout/
  semantic_readout_builder.py
  xin_definition_proxy.py
  readout_reporter.py
```

交付：外部读出结果只写 readout 表。

### Phase 3：Envelope 弱绑定

```text
bind_external_input_envelopes.py
real_input_desync_audit.py
```

交付：每个新增对象具备 envelope_ref；旧对象至少有 weak binding 或 missing report。

### Phase 4：Xin 调度与热浴

```text
triage_xin_against_principal_trajectory.py
transfer_to_topological_heat_bath.py
```

交付：前台/后台/延迟/热浴分类。

### Phase 5：R-band 受约束搜索

```text
build_r_band_candidates.py
score_r_band_cost.py
audit_pseudo_continuity.py
```

交付：不追求全局最优，只做 top-k 账本约束候选。

### Phase 6：外部模块扩展

```text
external_module_request
pde_like_solver_candidate
capacity_deficit_audit
```

交付：不求解 PDE，只发出外部模块请求与审计对象。

---

## 6. 第一版验收矩阵

```text
semantic_label_in_mainline = 0
xin_definition_inside_mainline = 0
external_readout_can_write_mainline = 0
readout_backwrite_blocked = 1
mainline_objects_have_envelope_ref >= configured threshold
xin_carriers_have_ledger_ref = 1
foreground_xin_budget_respected = 1
thermalized_xin_has_heat_bath_balance = 1
unregistered_meta_proxy_coefficients = 0
r_band_search_budget_respected = 1
pseudo_continuity_audit_enabled = 1
external_ledger_can_write_mainline = 0
```

---

## 7. 最小可运行版本的真正目标

最小版不是让系统“理解语义”，而是让系统重新回到早期原则：

```text
内部只产生物理/测度/轨迹/残余/账本结构；
外部模块后验读出语义；
语义不得反写主线；
Xin 在主线中只作为 carrier 存在；
递归链永远绑定外部真实输入包裹层。
```

这一步完成后，后续的变分作用量、R-band、Xin external leakage、PDE ghost、类神经 runtime 才不会污染主线本体。
