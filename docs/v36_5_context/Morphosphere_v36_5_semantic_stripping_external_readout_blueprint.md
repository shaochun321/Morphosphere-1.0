# Morphosphere v36.5 蓝图：上层递归去显式语义化与外部语义读出架构

**版本定位**：`v36.5_semantic_stripping_external_readout_envelope`  
**交付性质**：蓝图 / 设计约束 / 未来工程施工说明，不是工程实现。  
**核心命题**：Morphosphere 的上层递归系统（T/O/P/R/Xin 以及 attention、R-band、metric、hyperedge 等治理对象）不应在主线内部持有显式语义。语义应由外部模块从存储系统、外部账本、证据链、测度场和读出视图中后验判定。主线只保存物理—信息—账本—结构可计算对象。

---

## 0. 直接结论

你的早期原则仍然应该继续坚持，而且需要在当前阶段进一步收紧。

项目里曾经已经有这个方向：语义读出应是后验、只读、由物理量驱动，而不是根据字符串或名称直接贴标签；读出层不得修改来源对象或核心对象。这说明“语义不进入主线、只作为 readout”的原则并未完全丢失。

但目前最近几轮讨论又开始给 Xin、R-band、P-stasis、relative motion/rest、PDE ghost、external leakage 等对象赋予显式解释。这些解释对人类理解很有用，但如果直接进入上层递归主线，就会污染项目的物理计算架构。

因此 v36.5 的目标是：

```text
上层递归内部：
  不保存显式语义标签。
  不保存“意义”。
  不保存“理解”。
  不让语义驱动 P/R/O/Xin promotion。

外部模块：
  从存储、账本、测度、轨迹和 readout view 中后验判定语义。
  可输出 semantic readout。
  但只能只读、可撤销、可重算、可审计。
```

一句话：

> **Morphosphere 主线不理解语义；它只保存可计算的时空、测度、账本和残余。语义由外部模块读取，而不是由递归系统自封。**

---

## 1. 为什么必须剥离显式语义

### 1.1 显式语义会污染物理计算架构

T/O/P/R/Xin 的递归本应是物理—信息—测度—账本结构：

```text
T = trajectory / trace / transport carrier
O = object candidate / support organization / boundary assembly
P = positive support / confirmed measure / relative stasis support
R = counter-measure / continuity challenger / spacetime-band constructor
Xin = minimal unresolved residual carrier / ledger-attached nonclosure carrier
```

这些对象可以有功能角色，但不能在主线里带有显式语义，例如：

```text
运动
静止
生命
器官
意识
泄露
外部真实
PDE ghost
噪声
新异性
```

这些词可以出现在外部报告、readout、注释、蓝图解释里，但不应成为 active pipeline 的字段、分支条件、优化目标或 promotion 条件。

### 1.2 显式语义会导致自证闭环

如果主线内部保存语义：

```text
Xin.type = external_world_leakage
R.type = true_counter_motion
P.type = stable_life_structure
```

那么下一轮递归很容易把这些语义当作事实，从而：

```text
semantic label -> priority -> promotion -> stronger label -> higher priority
```

这会造成语义自激、自证、越权。

项目需要的是：

```text
storage state -> external readout -> report
```

而不是：

```text
semantic label -> internal dynamics -> semantic confirmation
```

### 1.3 显式语义会掩盖外部真实输入的更高支撑地位

内部递归是窗口化、异步、sidecar 化、ledger 化的工程切片。它不能忘记：数据总集仍然应被某种外部真实输入连续场包裹。

如果项目内部开始把递归链拆成自足的语义轨迹，它会误以为：

```text
内部时空轨迹 = 外部真实世界结构
```

这是必须避免的。内部轨迹只是对真实输入的工程切片和测度表达，不能替代外部真实时空的支撑。

---

## 2. 当前原则是否仍在坚持：阶段性判断

### 2.1 仍在坚持的证据

现有后验语义读出代码体现了三条正确原则：

```text
1. semantic readout 是后验读出层。
2. readout 使用物理量驱动，例如 maturity_flag、E_P、kappa，而不是表面字符串匹配。
3. readout strict rule: 不得修改输入的 family_surface 或 core objects。
```

这说明项目仍保留了“语义只读、后验、不得反写主线”的思想。

### 2.2 已经需要收紧的地方

但是，最近讨论中出现了大量解释性术语：

```text
external leakage Xin
capacity deficit
PDE closure ghost
relative motion / rest
cognitive field equation
semantic motion readout
Xin as cognitive boundary layer
```

这些概念在蓝图中有解释价值，但不能作为主线内生字段直接存在。它们必须被移到：

```text
external_xin_definition_module
external_semantic_readout_module
external_report_layer
```

主线只保留 minimal carrier 和审计引用。

---

## 3. 新架构总览

### 3.1 分层关系

```text
External Real World / Physical Input
  ↓
External Real-Input Continuity Envelope
  ↓
Raw Event / T Carrier
  ↓
T/O/P/R/Xin Upper Recursion Engine  ← no explicit semantics
  ↓
Storage + External Entropy Ledger + Hyperedge Sidecar
  ↓
External Readout Modules
  ├─ Semantic Readout
  ├─ Xin Definition Module
  ├─ R-band Interpretation Module
  ├─ Motion/Rest Relation Readout
  ├─ PDE-like Ghost Audit
  └─ Capacity Boundary Audit
  ↓
Human Report / Visualization / Documentation
```

### 3.2 核心规则

```text
主线可以生成：
  measure
  support
  residual
  trace
  trajectory
  cost
  budget
  ledger_ref
  carrier
  candidate
  state
  audit

主线不应生成：
  semantic label
  meaning
  ontology
  true motion
  true rest
  external leakage claim
  PDE claim
  biological claim
  consciousness claim
```

---

## 4. T/O/P/R/Xin 的无语义化重定义

### 4.1 T：trajectory carrier，不是“运动语义”

```text
T = windowed trace / transport / trajectory carrier
```

T 可以保存：

```text
source_refs
window_span
coordinate_trace
bandwidth
kernel_support
transport_cost
external_envelope_ref
```

T 不保存：

```text
this is motion
this is behavior
this is life-like action
```

### 4.2 O：support organization，不是“对象语义”

```text
O = support-domain assembly / boundary candidate / object carrier
```

O 可以保存：

```text
support_domain
boundary_proxy
membership_score
object_candidate_id
source_trace_refs
```

O 不保存：

```text
cell type
organ
agent
creature
meaningful entity
```

### 4.3 P：positive support measure，不是“真结构语义”

```text
P = confirmed support / relative stasis support / positive measure
```

P 可以保存：

```text
evidence_overlap
persistence
stasis_score
anchor_drift
ledger_balance_ref
```

P 不保存：

```text
truth
life
stable concept
semantic category
```

### 4.4 R：counter-continuity constructor，不是“反例语义”

```text
R = counter-measure / challenger chain / spacetime-band constructor
```

R 可以保存：

```text
r_band_candidate
continuity_cost
scale_switch_cost
kernel_switch_cost
ledger_budget
P_anchor_refs
```

R 不保存：

```text
opposition meaning
falsehood
anti-life
true counter motion
```

### 4.5 Xin：minimal residual carrier，不是“内部定义的未知本体”

```text
Xin = minimal carrier for unresolved, non-erasable, ledger-attached residual
```

Xin 可以保存：

```text
xin_carrier_id
source_T_refs
source_window_refs
support_domain_refs
residual_mass_proxy
ledger_ref
nonclosure_score
reentry_policy
external_definition_ref
attention_priority
```

Xin 不保存：

```text
external leakage
capacity deficit
PDE ghost
cognitive boundary layer
true anomaly
```

这些解释由外部模块判断。

---

## 5. Xin 的新权限边界

### 5.1 主线内部只保存 Xin carrier

主线只能说：

```text
这里有一片残余。
它随 T / O / P / R / window / support 出现。
它不能被当前主线合法闭合。
外部账本证明它不能被删除。
它可以被挂账、旁路、热浴化、re-entry 或交给外部模块解释。
```

主线不能说：

```text
这是外部世界泄露。
这是系统容量不足。
这是 PDE 幽灵。
这是真实物理。
这是新生命结构。
```

### 5.2 外部 Xin 模块负责解释

外部模块可以读出：

```text
external_leakage_candidate
capacity_deficit_candidate
pde_closure_ghost_candidate
continuity_failure_class
symmetry_closure_defect_class
mainline_defer_reason
```

但输出必须是：

```text
classification_ref
risk_level
confidence
readout_version
forbidden_interpretation
```

而不是主线事实。

---

## 6. 外部真实输入连续场包裹层

### 6.1 为什么需要这一层

项目内部是离散窗口、ledger、hyperedge、sidecar、sandbox、replay。它可能在内部看起来可以被拆解为许多独立轨迹，但真实输入并不是这些轨迹的从属物。

因此必须新增：

```text
External Real-Input Continuity Envelope
```

它的作用是提醒并约束：

```text
所有内部递归都来自外部输入的连续 / 准连续 / 真实过程包裹。
内部递归不能宣称独立于外部真实输入。
```

### 6.2 envelope 需要保存什么

```text
external_envelope_id
source_input_refs
sampling_window
clock_relation
real_input_desync_risk
continuity_assumption_level
external_modality
adapter_quality
noise_budget_ref
```

### 6.3 envelope 不保存什么

```text
真实世界本体定义
语义标签
物理真理
生命/意识/行为解释
```

---

## 7. 语义外部化架构

### 7.1 Storage-first readout

语义模块不读取主线语义字段，因为主线不应有这些字段。它读取：

```text
storage states
coordinate traces
support domains
ledger events
hyperedge incidence
metric proxies
xin carriers
R-band candidates
P stasis profiles
O support assemblies
```

然后输出只读 readout。

### 7.2 外部语义读出模块

建议外部模块分为：

```text
external_semantic_readout_module
external_xin_definition_module
external_relation_readout_module
external_continuity_interpretation_module
external_pde_like_audit_module
external_capacity_boundary_module
```

### 7.3 readout 输出必须带禁止解释

每个 readout 必须有：

```text
readout_id
readout_type
source_storage_refs
feature_view_hash
classification
confidence
readout_version
external_module_version
forbidden_interpretation
writeback_allowed = 0
```

---

## 8. 新增 schema 草案

### 8.1 `v365_upper_recursion_semantic_null_contract`

记录上层递归对象的无语义契约。

| 字段 | 说明 |
|---|---|
| contract_id | 契约 ID |
| object_family | T / O / P / R / Xin / attention / metric / hyperedge |
| allowed_fields | 允许字段类别 |
| forbidden_semantic_fields | 禁止字段类别 |
| enforcement_level | warn / block / fail_acceptance |
| created_at | 时间 |

### 8.2 `v365_xin_minimal_carrier_state`

主线内部最小 Xin 承载。

| 字段 | 说明 |
|---|---|
| xin_carrier_id | Xin carrier ID |
| source_T_refs | 来源 T 引用 |
| source_OPR_refs | O/P/R 相关引用 |
| window_span | 窗口范围 |
| support_refs | 支撑域引用 |
| residual_mass_proxy | 残余质量 proxy |
| ledger_ref | 外部账本引用 |
| foreground_status | foreground/background/deferred/thermalized |
| reentry_policy | via_T / via_O_candidate / external_module_only / blocked |
| external_definition_ref | 外部解释引用，可为空 |

### 8.3 `v365_external_xin_definition_ref`

外部 Xin 模块输出引用。

| 字段 | 说明 |
|---|---|
| definition_ref | 外部定义引用 |
| xin_carrier_id | Xin carrier |
| module_name | 外部模块名 |
| classification_code | 类型码，不写入主线 |
| confidence | 置信度 |
| risk_level | 风险级别 |
| recommended_handling | defer / heat_bath / reentry / external_adapter_request |
| forbidden_interpretation | 禁止解释 |
| writeback_allowed | 必须为 0 |

### 8.4 `v365_external_real_input_envelope_binding`

外部真实输入包裹层绑定。

| 字段 | 说明 |
|---|---|
| envelope_id | 包裹层 ID |
| source_input_refs | 外部输入引用 |
| bound_object_ref | T/O/P/R/Xin/metric/hyperedge 引用 |
| continuity_assumption | none / weak / quasi_continuous / continuous_proxy |
| desync_risk | 内部递归与真实输入脱节风险 |
| adapter_quality | adapter 质量 |
| noise_budget_ref | 噪声预算引用 |

### 8.5 `v365_external_semantic_readout_result`

外部语义读出结果。

| 字段 | 说明 |
|---|---|
| readout_id | 读出 ID |
| source_storage_refs | 存储引用 |
| feature_view_hash | 特征视图哈希 |
| semantic_output | 外部读出标签 / 描述 |
| confidence | 置信度 |
| readout_version | 版本 |
| writeback_allowed | 必须为 0 |
| valid_until | 可过期 |
| superseded_by | 可替换 |

### 8.6 `v365_semantic_contamination_audit`

扫描主线是否被语义污染。

| 字段 | 说明 |
|---|---|
| audit_id | 审计 ID |
| object_ref | 被审计对象 |
| offending_field | 可疑字段 |
| semantic_keyword | 语义关键词 |
| severity | warn / block / fail |
| remediation | move_to_external_readout / rename_to_proxy / remove |

### 8.7 `v365_readout_backwrite_block_event`

阻断外部语义反写。

| 字段 | 说明 |
|---|---|
| event_id | 事件 ID |
| readout_id | 来源 readout |
| attempted_target | 试图写入对象 |
| blocked_reason | 阻断原因 |
| timestamp | 时间 |

---

## 9. 算法流程

### 9.1 Semantic stripping lint

```text
for each active table / schema / runtime payload:
    scan field names, enum values, comments, rule names
    if field implies semantic label:
        register semantic_contamination_audit
        if active pipeline field:
            block acceptance
        else if report/readout layer:
            allow only if writeback_allowed = 0
```

### 9.2 External semantic readout

```text
input:
  storage refs
  ledger refs
  metric refs
  carrier refs
  feature view config

process:
  build feature view from storage
  compute external semantic classification
  bind readout to source refs
  mark writeback_allowed = 0

output:
  readout result
  confidence
  forbidden interpretation
```

### 9.3 Xin external definition

```text
for each xin_carrier:
    gather source T / O / P / R refs
    gather ledger closure status
    gather envelope binding
    external module produces classification_ref
    mainline stores only external_definition_ref
    no direct rewrite to Xin carrier facts
```

### 9.4 Real-input envelope guard

```text
for each T/O/P/R/Xin trajectory:
    require external_envelope_ref
    compute real_input_desync_risk
    if missing envelope_ref:
        fail acceptance
    if desync risk high:
        downgrade readout confidence
```

---

## 10. 降级 / 最小化 / 修正契约

| 原哲学—数学构想 | 不能直接采用的原因 | 降级后的工程对象 | 最小化 / 修正机制 | 禁止解释 |
|---|---|---|---|---|
| 上层递归完全无语义 | 工程上仍需要报告、调试、用户理解 | `semantic_null_contract` + external readout | 主线无标签，外部只读读出 | 不等于系统无可解释性 |
| 语义由外部模块判定 | 外部模块也可能漂移 | `external_semantic_readout_result` | 版本化、置信度、可过期、不可反写 | 不等于语义真理 |
| Xin 的定义移出主线 | 主线仍需处理 residual | `xin_minimal_carrier_state` | 主线只保存 carrier / ledger / reentry | 不等于 Xin 不存在 |
| 外部真实输入连续场 | 当前没有真实连续 runtime | `external_real_input_envelope_binding` | envelope_ref + desync audit | 不等于已建模真实世界 |
| T/O/P/R/Xin 递归连续场 | 内部实现仍是离散窗口 | `continuous_field_envelope_proxy` | 外部包裹 + 内部离散双视图 | 不等于内部已经连续化 |
| 语义标签全部剥离 | 部分 legacy readout 已存在标签字段 | `legacy_semantic_readout_quarantine` | 迁移到 external readout layer | 不在 active pipeline 使用 |
| “外部泄露 / PDE ghost”等解释 | 显式语义过强 | `external_definition_ref` | 只存外部解释引用 | 不写入 P/R/O/Xin 主线 |
| 语义读出可用于人类报告 | 容易反馈进系统 | `readout_backwrite_block` | writeback_allowed = 0 | 不得影响 promotion |

---

## 11. 悬置项

以下概念必须悬置，不能进入 active pipeline：

```text
1. 真实语义理解。
2. 真实外部世界本体建模。
3. 生命 / 意识 / 意图 / 行为的主线内部定义。
4. Xin 的本体类型学。
5. PDE ghost 的物理方程识别。
6. 真实运动 / 静止标签。
7. 语义驱动的 P/R/O promotion。
8. 外部 readout 反写内部递归。
```

这些可以作为外部报告词汇、研究假设或未来模块接口，但不得成为当前上层递归的计算对象。

---

## 12. 否决项

以下设计应明确否决：

```text
1. 在 T/O/P/R/Xin 表中加入 semantic_label 字段。
2. 让 LLM 直接给 P/R/O/Xin 分类并写回主线。
3. 把 external_leakage、PDE_ghost、life_like、motion/rest 写成主线枚举。
4. 用 semantic label 作为 promotion、memory、macro-node、attention priority 的直接条件。
5. 让外部语义模块改写 source facts、P/R/Xin、origin anchor、coordinate trace。
6. 让 readout confidence 影响主线物理测度。
7. 把语义解释当作 ledger closure。
```

---

## 13. Acceptance 标准

```text
1. 所有 active T/O/P/R/Xin schema 中不得出现 semantic_label、meaning、life、motion、static、external_leakage、PDE_ghost 等显式语义字段。

2. 所有语义输出必须位于 external_readout 命名空间或 report 层。

3. 所有 semantic readout 必须 writeback_allowed = 0。

4. 所有 Xin 解释必须通过 external_definition_ref 引用，主线不得保存分类本体。

5. 所有 T/O/P/R/Xin 轨迹必须绑定 external_envelope_ref 或说明缺失原因。

6. 缺失 external envelope 的主线轨迹不得进入 high-confidence readout。

7. semantic_contamination_audit 若发现 active pipeline 使用语义字段，acceptance 失败。

8. legacy semantic readout 必须被标记为 readonly/quarantined/externalized。

9. 任何数学高阶概念进入工程前，必须有 downgrade contract、悬置说明和否决说明。
```

---

## 14. 与最近讨论的整合

### 14.1 Xin

近期我们讨论了 Xin 的多种解释：连续性失败、外部泄露、容量不足、PDE ghost、代数—几何解耦、主线无法处理的边界层。这些解释全部保留，但只能进入外部 Xin module。

主线只保留：

```text
xin_minimal_carrier_state
```

### 14.2 R-band

R 仍可作为跨尺度时空带构造者，但 R-band 不能自称“真实连续轨迹”。外部模块可以从 R-band 的 cost、ledger、Xin residual 中读出“可能的语义解释”。

### 14.3 P-stasis

P 仍可作为相对静止支撑，但不能在主线内部写成“静止语义”。外部 relation readout 可以根据稳定测度模式输出相对静止读出。

### 14.4 信息—能量测度

信息—能量测度可以作为关系度规 proxy，但不能直接生成语义标签。测度模式只能被外部 readout 读取。

### 14.5 外部真实输入包裹层

这是本轮新增的核心：内部递归不是自足世界。所有内部轨迹必须保留对外部真实输入连续场包裹层的引用。

---

## 15. 未来版本建议

### v36.5

```text
Semantic Stripping + External Readout + Real-Input Envelope
```

目标：完成上层递归去显式语义化、Xin 外部定义、external envelope guard。

### v36.6

```text
Xin External Definition Module
```

目标：把 external leakage、capacity deficit、PDE ghost、continuity failure 等解释放入外部模块。

### v37

```text
External Module Interface + Storage-Derived Readout Runtime
```

目标：构建从存储系统生成外部语义读出的标准接口。

---

## 16. 最终原则

```text
主线负责生成可审计结构；
外部模块负责解释结构；
外部账本负责约束解释；
真实输入包裹层负责提醒系统不要忘记外部世界。
```

最终一句话：

> **Morphosphere 的上层递归不应“理解”语义。它应产生足够干净、可审计、可回投、可账本化的结构，使外部模块能够从存储系统中后验读出语义。**
