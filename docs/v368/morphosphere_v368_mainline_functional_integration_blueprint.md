# Morphosphere v36.8 工程蓝图与方案准则

**版本定位**：`v36.8_mainline_functional_integration`  
**文档性质**：工程蓝图 + 行为准则 + 数理判据  
**目标读者**：后续 AI、工程执行者、项目审查者  
**核心约束**：本版本不新增宏大理论对象，不宣布 Online Native Runtime，不改写旧 DB 主线事实。v36.8 的目标是把最近 v36.7.x 的硬化成果重新服务于主线：信息时空轨迹、T/O/P/R/Xin、反证/屏蔽、外部账本、attention、hyperedge、variational、Xin carrier/readout。

---

## 0. 总决策

v36.7.1-v36.7.5 主要完成了工程硬化：native anchor baseline、safe stress guard、semantic quarantine、RMI default index、release gate。它们提高了可运行性、可追溯性、可审计性，但不应继续主导项目叙述。

v36.8 的任务是回到主线：

```text
source information point
  -> 3D/4D backprojection
  -> trajectory / T window
  -> O candidate / support candidate
  -> P / R / Xin role split
  -> counter-evidence / masking
  -> external entropy ledger
  -> attention
  -> hyperedge
  -> variational path / Xin_var
  -> Xin carrier / external readout
```

v36.8 要回答的不是“包是否可部署”，而是：

```text
1. 信息经过每层后实际发生了什么状态变化？
2. T/O/P/R/Xin 分离的判据是什么？
3. 哪些模块改变信息状态，哪些只是索引、guard、外部读出或测试？
4. 最近硬化层是否真的服务主线？
5. 下一阶段若进入 v37，哪些条件必须先满足？
```

---

## 1. 行为总准则

### 1.1 五类模块位置

所有新增对象、脚本、DB 表必须先归类。

| 分类 | 是否主线 | 作用 | 例子 |
|---|---:|---|---|
| `MAINLINE_STATE_TRANSFORM` | 是 | 改变信息状态或角色 | trajectory -> P/R/Xin，R -> R-band，Xin -> carrier |
| `EVIDENCE_ANCHOR` | 支撑主线 | 证明状态变化可回投 | information point，trajectory window，native anchor fact |
| `GOVERNANCE_LEDGER` | 支撑主线 | 约束、审计、预算 | external entropy ledger，Noether audit proxy |
| `EXTERNAL_READOUT` | 否 | 只读解释、分类、假设 | external Xin definition，semantic readout |
| `OPERABILITY_LAYER` | 否 | 测试、部署、索引、guard、查询 | RMI index，safe stress guard，CI gate，query script |

行为规则：

```text
如果一个模块不能改变 trajectory / role / ledger / attention / carrier 状态，
它不能被称为主线能力提升。
```

### 1.2 禁止事项

```text
禁止把 RMI 检索提升称为认知本体。
禁止把 safe stress guard 称为新的 P/R/Xin 分离机制。
禁止把 semantic quarantine 称为主线语义理解。
禁止把外部 readout 反写成 P/R/Xin truth。
禁止把 materialized integration 说成 online native runtime。
禁止把 L2 anchor candidate 伪装成 legacy raw direct FK。
```

### 1.3 允许事项

```text
允许新增非破坏性 overlay DB。
允许构建 mainline functional audit。
允许把 v36.7 hardening 作为 evidence anchor / operability layer 引用。
允许做 source-level rerun / stress / generalization。
允许外部 readout 产生只读解释，但必须写入 external sidecar。
```

---

## 2. v36.8 主线功能目标

v36.8 要建立一个主线功能审计层：

```text
m368_mainline_functional_integration.db
```

它不替代旧 DB，不改写 v25-v36.7 数据，而是新增可查询视图：

```text
v368_mainline_trace
v368_toprxin_state_transition
v368_information_change_attribution
v368_module_role_contract
v368_external_module_boundary
v368_hardening_to_mainline_utility
v368_math_proxy_registry
v368_acceptance_report
```

其中最关键的是：每一个信息状态变化都要有 cause vector。

```text
cause_vector = {
  geometry_delta,
  support_delta,
  ledger_delta,
  counter_evidence_delta,
  masking_delta,
  residual_delta,
  attention_delta,
  readout_delta
}
```

只有当 cause_vector 中存在有效变化时，才能说该模块改变了主线状态。

---

## 3. 数理基础：从观测点到信息时空轨迹

### 3.1 信息点

一个信息点定义为：

```text
p_i = (sequence_id, frame_t, raw_x, raw_y, optional_z, area, track_id, source_digest)
```

它不是语义对象，只是带来源的观测事实。

### 3.2 坐标回投与不变性

刚性平移：

```text
x'_i = x_i + a
y'_i = y_i + b
```

任意两点距离：

```text
||p'_i - p'_j|| = ||(x_i+a, y_i+b) - (x_j+a, y_j+b)||
                 = ||(x_i-x_j, y_i-y_j)||
```

因此 path length、net displacement、direction coherence 在刚性平移下应不变。若 P/R/Xin 因刚性平移系统性改变，说明主线错误依赖绝对坐标。

验收：

```text
rigid_translation_role_changed = 0
max_relative_path_delta < epsilon
```

### 3.3 轨迹窗口

一个轨迹窗口：

```text
T_j = {p_i | t_start <= frame_i <= t_end, track_id = k}
```

基础几何量：

```text
path_length(T_j) = Σ_i ||p_{i+1} - p_i||
net_displacement(T_j) = ||p_last - p_first||
duration(T_j) = t_end - t_start + 1
mean_speed(T_j) = path_length / duration
direction_coherence(T_j) = net_displacement / max(path_length, ε)
```

含义：

```text
coherence 接近 1：方向一致，轨迹较直。
coherence 接近 0：局部震荡、回返或支撑不稳定。
```

---

## 4. Process Window 的主线定义

v36.8 继续使用 process_window，但它不应被当成抽象口号。它必须可以拆为：

```text
W_k = (I_k, T_k, S_k, Π_k, E_k, L_k)
```

| 符号 | 含义 | 必须可查字段 |
|---|---|---|
| `I_k` | information payload / measure contribution | information_point_ref, evidence_bundle_ref |
| `T_k` | time span / ordering | frame_start, frame_end, sequence_id |
| `S_k` | support domain / kernel | trajectory_window_ref, support_domain_ref |
| `Π_k` | process operators / recursion trace | operator_trace_ref, state_transition_ref |
| `E_k` | external input envelope | external_envelope_ref |
| `L_k` | ledger balance ref | ledger_window_ref |

行为准则：

```text
process_window 是主线工作单位；
RMI 是它的索引；
native anchor 是它的证据锚；
guard 是它的运行保护；
readout 是它的外部解释。
```

---

## 5. T/O/P/R/Xin 的数理代理

### 5.1 T：过程连续性

T 层判据：

```text
T_score = f(path_length, duration, coherence, support_persistence, transport_cost)
```

约束：

```text
T_score 不得使用语义标签。
T_score 应对刚性平移不变。
T_score 可对非刚性扭曲产生局部响应。
```

### 5.2 O：支撑候选

O 不是语义 object，而是 support candidate：

```text
O_candidate = cluster_or_window_support(T_j, S_j)
```

它只回答：

```text
这组轨迹/窗口是否可作为 P/R/Xin 审判承载面？
```

### 5.3 P：稳定支撑

P 的代理形式：

```text
P_score = α1 * support_persistence
        + α2 * prediction_mass
        + α3 * masking_survival_ratio
        + α4 * ledger_closure_quality
        - α5 * curvature_instability
        - α6 * unexplained_residual_mass
```

行为准则：

```text
P 是相对稳定支撑，不是真实物体、不是真理标签。
P_core 对低/中等边界扰动应保持稳定。
P_boundary 可以被 R 反证挑战。
```

### 5.4 R：反证结构

R 的代理形式：

```text
R_pressure = β1 * p_displacement_mass
           + β2 * masking_exposure_gain
           + β3 * entropy_violation_mass
           + β4 * counter_evidence_density
           + β5 * recursive_reentry_priority
```

结构化反证注入应满足：

```text
∂R_pressure / ∂counter_injection >= 0
```

但同时要求：

```text
P_core_collapse = 0   under safe envelope
```

### 5.5 Xin：未闭合残余

Xin 不等于噪声。v36.8 继续采用：

```text
Xin_var = el_residual_proxy
        + ledger_balance_residual
        + constraint_violation
        + unresolved_anomaly_mass
```

Xin 的行为准则：

```text
如果 R 能形成连续反证链，优先进入 R-band，而不是直接进入 Xin。
如果残余无法被 P/R/O 接纳，但 ledger 不能归零，则进入 Xin carrier。
如果 residual 低 SNR，则可 thermalized / deferred。
```

---

## 6. 上层模块如何改变信息

信息状态变化链：

```text
point -> trajectory -> role vector -> counter/mask -> ledger -> attention -> hyperedge -> variational -> carrier/readout
```

其中 role vector 定义为：

```text
r_k = [P_score, R_pressure, Xin_var]
```

状态转移：

```text
Δr_k = r_k(t+1) - r_k(t)
```

主线变化必须能归因：

```text
Δr_k = A_geometry + A_support + A_ledger + A_counter + A_masking + A_residual + A_attention
```

如果某模块只改变查询速度、部署状态或报告文字，则不计入 Δr_k。

---

## 7. Attention、Hyperedge、Variational 的行为准则

### 7.1 Attention

Attention tension 代理：

```text
attention_tension = wP * P_mass
                  + wR * R_counter_mass
                  + wX * Xin_residual_mass
                  + wA * anomaly_mass
                  - wB * boredom_decay
```

行为准则：

```text
attention 是资源分配，不是行动，不是真理。
attention 提升应能追溯到 P/R/Xin/anomaly/boredom 的变化。
```

### 7.2 Hyperedge

Hyperedge 表达高阶共现：

```text
H_e = {node_1, node_2, ..., node_n}, n >= 3
```

行为准则：

```text
hyperedge 是多主体绑定事件，不是语义图谱。
hyperedge weight 不是 truth，只是 ledger/proxy support。
hyperedge 必须通过 native anchor 或 materialized anchor 回投到底层 evidence。
```

### 7.3 Variational path

路径代价：

```text
S_IE_proxy(Γ) = metric_kinetic_proxy
              + dissipation_cost
              + noise_cost
              + anomaly_cost
              + r_counter_cost
              + xin_mass_cost
              + noether_violation_cost
              - legal_source_credit
```

离散 stationarity defect：

```text
D_stat = |2*S_current - S_left - S_right| / 2
```

行为准则：

```text
S_IE_proxy 是路径排序代理，不是自然定律。
D_stat 是离散扰动缺陷，不是解析 Euler-Lagrange 证明。
```

---

## 8. 外部模块行为准则

外部模块包括：

```text
external Xin definition
external semantic readout
classification / hypothesis / risk readout
semantic quarantine sidecar
```

允许：

```text
read mainline carrier
read ledger refs
write readout_result
write definition_ref
write hypothesis_ref
write risk_flag
write reentry_suggestion
```

禁止：

```text
write source facts
write P/R/Xin truth
write semantic label to mainline
turn readout into O/P/R/Xin directly
```

判据：

```text
semantic_write_allowed = 0
external_readout_writes_mainline = 0
```

---

## 9. 工程硬化层的正确定位

### 9.1 Native anchor

作用：证明上层对象可以回到底层 evidence。

不是：新的认知机制。

### 9.2 RMI index

作用：提高关系检索效率，降低 false-neighbor 风险。

不是：替代信息时空轨迹。

RMI H3 推荐输入：

```text
H3 = HASH(
  quantized_mu_IE,
  entropy_gap_bin,
  dark_grid_zone_id,
  sequence_id,
  frame_bin,
  trajectory_window_ref,
  information_point_ref or process_window_ref
)
```

### 9.3 Safe stress guard

作用：阻止已知危险压力组合导致 P-core collapse。

不是：新的 P/R/Xin 计算公式。

### 9.4 Semantic quarantine

作用：防止解释性文本进入主线计算路径。

不是：语义理解。

---

## 10. v36.8 工程范围

### 必须构建

```text
m368_mainline_functional_integration.db
v368_mainline_trace
v368_toprxin_state_transition
v368_information_change_attribution
v368_module_role_contract
v368_external_module_boundary
v368_hardening_to_mainline_utility
v368_math_proxy_registry
v368_acceptance_report
```

### 可选构建

```text
v368_sample_trajectory_casebook
v368_stress_effect_comparison
v368_ctc01_02_mainline_comparison
```

### 不构建

```text
online native runtime
Faiss/vector DB runtime
100ms coordinate audit
complex-valued async recursion
new PDE/continuous field
new semantic ontology
```

---

## 11. 验收标准

### A. 主线 trace 覆盖

```text
mainline_trace_rows >= 532
sample_full_trace_rows >= 20
```

### B. 状态转移归因

```text
每条 TOPRXin transition 必须有 cause_vector。
```

### C. 模块分类

```text
每个模块必须标注：MAINLINE_STATE_TRANSFORM / EVIDENCE_ANCHOR / GOVERNANCE_LEDGER / EXTERNAL_READOUT / OPERABILITY_LAYER。
```

### D. 外部模块边界

```text
semantic_write_allowed = 0
external_readout_writes_mainline = 0
```

### E. 硬化层不得冒充主线

```text
RMI / guard / CI / deploy / query script 不得计为 mainline state transform。
```

### F. 数理代理登记

```text
P_score, R_pressure, Xin_var, attention_tension, S_IE_proxy, D_stat, RMI_H3 必须登记到 math_proxy_registry。
```

---

## 12. 下一阶段行为指导

每次新增构建前必须回答：

```text
1. 它改变了信息状态吗？
2. 它改变的是 P/R/Xin、attention、hyperedge、variational、readout 中哪一层？
3. 它的输入是什么？输出是什么？
4. 它的数理代理是什么？
5. 它是否依赖语义文本？
6. 它能否回投到底层 evidence？
7. 它是主线能力、证据锚、外部模块、guard、索引，还是交付工具？
```

如果回答不清楚，则只能进入 advisory 或 operability layer，不能进入主线。

---

## 13. 与 v36.7.5 的关系

v36.7.5 已经提供：

```text
native anchor baseline
safe stress guard config
semantic quarantine
RMI default index
release gate
```

v36.8 的任务是把这些硬化结果重新映射回主线：

```text
native anchor -> 证明 TOPRXin/hyperedge/readout 可回投
safe guard -> 保护 P-core，不创造新角色
semantic quarantine -> 保证 readout 不污染主线
RMI -> 加速关系查找，不替代轨迹
release gate -> 交付门禁，不代表主线能力
```

---

## 14. 最终原则

v36.8 的最终原则：

```text
少构建外围，多解释主线。
少说部署，多说信息如何变化。
少说通过，多说识别与分离的数理原因。
少把工具当能力，多把工具归位。
```

一句话：

> v36.8 不是继续硬化数据库，而是重新证明 Morphosphere 的核心主线：信息如何从观测点变成时空轨迹，再被 T/O/P/R/Xin 分解、被账本约束、被 attention 和 hyperedge 组织、被 variational 路径评分，最后以 Xin carrier / external readout 的形式进入外部只读解释层。
