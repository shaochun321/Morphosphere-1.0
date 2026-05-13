# Morphosphere v35 蓝图：注意力治理与外部熵正本路径积分审计

**版本定位**：`v35_attentional_path_integral_governance`  
**交付性质**：施工蓝图，不是代码实现。  
**基线版本**：v34 / v34.1 的 Proxy Control Plane、External Entropy Ledger Plane、Meta-Proxy Governance、Runtime Guard。  
**核心命题**：在 v34.1 完成“治理系统自身的治理”之后，Morphosphere 需要开始回答一个更接近生命系统的问题：**系统应该把有限的认知资源投向哪里？**

v35 不是普通意义上的 attention layer。它不是 Transformer 的 query-key-value 权重，也不是一个全局注意力分数表。v35 的注意力是一个受外部熵正本、Proxy 宪法、Runtime Guard 和路径积分审计约束的 **认知资源分配提案系统**。

简写：

```text
v35 = Attention Proposal Sandbox
    + Counter-evidence / Masking / P-R Trajectory Competition
    + External Entropy Ledger Path Integral Auditor
```

---

## 0. 执行摘要

v25-v33 让系统完成了三件事：

```text
真实 evidence 可追踪
shadow / prediction 可审判
legacy bottom 可作为 prediction source 回归
```

v34-v34.1 又完成了两件事：

```text
Proxy 不再可以越权冒充真理
外部熵账本不再只是装饰，而成为等效能量、耗散、噪声和异常的外部正本
```

但是系统仍然缺少一个关键能力：**在有限计算资源下选择“看哪里”。**

如果没有注意力治理，系统会出现四种失败模式：

1. **全域平铺失败**：所有窗口、所有轨迹、所有 Xi 都被同等处理，计算成本爆炸。
2. **强 P 独占失败**：已确认 P 结构长期占据注意力，系统忽略粘合外的新异信号。
3. **噪声劫持失败**：高波动但低结构性的异常把系统拖入伪新异性。
4. **注意力黑箱失败**：注意力模块本身成为新的 proxy 权力中心。

v35 的目标是建立一个白盒注意力系统：

```text
注意力来源要可追溯
注意力提案要有 proxy 身份
注意力转移要经过外部熵正本路径积分审计
注意力效果要能被 P/R/Xi、anomaly、dissipation、SNR 共同解释
注意力不能改写 source facts
```

---

## 1. 版本边界

### 1.1 v35 做什么

v35 做以下事情：

```text
1. 从 v28/v28.1/v30/v33/v34 中抽取候选注意力区域。
2. 计算 P/R/Xi/anomaly/masking 共同形成的 attention tension。
3. 生成 sandbox-only attention proposals。
4. 允许 masking proposal 在沙盒中测试稳健性。
5. 对注意力转移路径执行外部熵正本路径积分审计。
6. 输出 attention performance report。
7. 标记 novelty candidate，但不自动提升为 P/R/O。
```

### 1.2 v35 不做什么

v35 明确不做以下事情：

```text
1. 不授权真实行动。
2. 不改写 source facts。
3. 不让 attention proposal 直接改写 P/R/Xi。
4. 不把 path integral 最小化解释为 scientific truth。
5. 不把 external ledger energy 解释为物理焦耳能量。
6. 不把 attention verdict 解释为生物学结论。
7. 不开启全局可微优化。
```

v35 的所有注意力对象都是 **proposal / audit / sandbox / proxy-derived**。

---

## 2. 继承关系：v25-v34.1 到 v35

| 上游版本 | 提供给 v35 的内容 | v35 如何使用 |
|---|---|---|
| v25 Evidence Store | information point、coordinate trace、trajectory window、P/R/Xi measure | 作为注意力候选区域的 evidence 根 |
| v26 Shadow | shadow cell、shadow edge、shadow motion | 作为 prediction/contrast source |
| v27 Reversible Query | point/trajectory/measure query index | 支持 attention proposal 反查证据链 |
| v28 Divergence Gate | confirmed P、overreach、surprise Xi、emergence candidate | 生成 P/R/Xi 张力项 |
| v28.1 Robustness | precision weight、control experiment、entropy coupling | 提供 SNR / robustness 权重 |
| v29 Sandbox | intervention proposal、sandbox replay | 为未来 attention-action coupling 做接口 |
| v30 Macro Node | macro-node candidate、cross-level attention request | 提供宏观吸引子 |
| v31 Policy Loop | policy posterior、expected free-energy proxy | 提供策略上下文，但不授权 action |
| v32 Source Adapter | general source event、scale contract | 统一多来源注意力区域 |
| v33 Bottom Prediction | bottom prediction event/edge、entropy constraint prediction | 将 legacy bottom 的预测纳入注意力竞争 |
| v34 Proxy × Entropy | proxy registry、external ledger、Noether audit、binding | 路径积分审计的外部正本 |
| v34.1 Meta-Proxy | runtime guard、SNR-first、governance mode、gradient path audit | 防止注意力/积分/账本自身越权 |

---

## 3. 哲学定位

### 3.1 注意力不是权力，而是问责式选择

在 Morphosphere 中，注意力不是“系统想看哪里就看哪里”。注意力必须回答：

```text
为什么看这里？
谁提出这个注意力？
它依赖哪些 proxy？
它消耗了多少外部账本资源？
它带来结构性新异，还是只是噪声劫持？
```

所以 v35 的 attention 是一种 **可问责的认知资源提案**。

### 3.2 注意力不是行动，但它是行动的预备姿态

行动意味着改变世界；注意力意味着选择性地观察、重放、加精度、屏蔽或重新分配资源。

v35 仍处于行动之前：

```text
Attention Proposal
  -> sandbox replay / masking / path integral audit
  -> performance report
  -> future policy hint
```

它不能直接进入：

```text
Attention Proposal -> source facts rewrite
```

### 3.3 外部熵正本不是优化器，而是裁判

外部熵账本在 v35 中提供路径积分裁判，但它不是内部优化器。外部账本中的能量是：

```text
ledger energy / effective energy / free-energy-like quantity
```

它不能被解释为：

```text
physical joule energy
biological free energy
scientific variational free energy
```

### 3.4 路径积分不是物理宣称，而是路径级审计

v35 引入 path integral，但这是 **ledger-level path integral**，不是量子力学或真实物理路径积分的直接实现。

它的作用是量化一条注意力路径上的：

```text
外部自由能账变化
耗散累积
噪声累积
异常质量
Noether-style violation
结构性信噪比
```

它回答的是：

```text
这条注意力路径是否值得继续？
是否只是噪声？
是否暴露了持久新异？
是否在账本上造成不可解释的无理由增值/损失？
```

---

## 4. 理论映射：成熟理论与 Morphosphere 对应关系

### 4.1 Predictive Coding

成熟理论中的 predictive coding 将高层预测和低层 prediction error 组织成循环。Morphosphere 中的对应关系是：

| Predictive Coding | Morphosphere |
|---|---|
| top-down prediction | Shadow / bottom prediction / policy prior |
| bottom-up error | Evidence-Shadow divergence / Xi surprise |
| precision weighting | v28.1 precision / v35 attention tension |
| prediction error routing | R-counterstructure / Xi residual / anomaly ledger |

v35 对应的是：**决定哪些 prediction error 值得继续处理**。

### 4.2 Active Inference

Active inference 区分 perception 与 action 两种降低 free-energy / surprise 的路径。Morphosphere 目前仍不做真实 action；v35 是 action 前的 attention layer。

| Active Inference | Morphosphere |
|---|---|
| expected free energy | expected-free-energy proxy / ledger path score |
| policy selection | v31 policy posterior / v35 attention proposal |
| action | v29 sandbox intervention only |
| precision | v28.1 / v35 SNR path weighting |

v35 不宣称实现完整主动推理，只实现 **attention-governed policy preselection**。

### 4.3 Markov Blanket

Markov blanket 将内部状态与外部状态通过感官/行动边界分开。Morphosphere 中更适合把它理解为 **时空粘合后的屏蔽边界**。

```text
macro P/R trajectory cluster
  -> internal state
boundary leakage / anomaly / Xi
  -> sensory boundary
masking / attention proposal
  -> active boundary proposal
```

v35 中的 masking 和 boundary leakage audit 是马尔可夫毯思想的工程近似。

### 4.4 Renormalization Group / Coarse Graining

随着递归次数增加，局部有限差分、局部散度、局部 P/R 竞争可能固化为更高层稳固节点。这对应重整化思想：

```text
micro-difference
  -> repeated recurrence
  -> stable mesoscale pattern
  -> macro-node candidate
```

v35 暂不执行完整宏观重整化，但它通过注意力选择机制，为 v36 的宏观粘合与屏蔽层准备候选。

### 4.5 Path Integral / Least Action

v35 不直接计算真实物理 action，而是使用外部账本定义 ledger action：

```text
S_ledger[path] = Σ ledger_cost(window)
```

它借鉴“路径整体优于局部贪心”的思想：不要只看单窗口最小 divergence，而要看一条注意力路径上的总账、耗散、异常与新异性。

---

## 5. 核心数学对象

### 5.1 基本集合

令：

```text
W = {w_1, ..., w_T}               时间窗口集合
R = {r_1, ..., r_N}               候选时空区域集合
P(r, w)                           区域 r 在窗口 w 的 confirmed P 质量
R_c(r, w)                         区域 r 在窗口 w 的 R-counter mass
Xi(r, w)                          区域 r 在窗口 w 的 Xi residual mass
A(r, w)                           区域 r 在窗口 w 的 anomaly mass
M(r, w)                           区域 r 在窗口 w 的 masking exposure
F_ext(w)                          外部自由能账
D(w), N(w), A_ext(w)              外部耗散、噪声、异常账
```

### 5.2 注意力张力

对候选区域 `r` 在窗口 `w` 的注意力张力定义为：

```text
T_attn(r,w) =
    a_P   * P(r,w)
  + a_R   * R_c(r,w)
  + a_Xi  * Xi(r,w)
  + a_A   * A(r,w)
  + a_M   * M(r,w)
  - a_B   * Boredom(r,w)
  - a_C   * ComputeCost(r,w)
```

其中：

```text
Boredom(r,w) = stability_duration(r,w) * low_anomaly_factor(r,w)
```

解释：

- 高 P 质量会吸引注意力，因为它是稳定内部模型。
- 高 R / Xi / anomaly 也会吸引注意力，因为它可能挑战或拓展当前模型。
- 高 boredom 会降低注意力，因为长期稳定且无异常的区域不应永久占用资源。
- 高 compute cost 会惩罚注意力提案，防止全域扩张。

### 5.3 P 轨迹惯性

稳定 P/R 时空轨迹具有惯性：

```text
I_P(τ) =
    b_1 * duration(τ)
  + b_2 * internal_coherence(τ)
  + b_3 * repeated_confirmation_count(τ)
  + b_4 * low_divergence_history(τ)
```

惯性越高，越不容易被单次 Xi 或噪声击穿。

### 5.4 反证链动量

反证链不是单次异常。反证链需要跨窗口连续、空间上重合、方向上稳定。

```text
Momentum_Xi(C) =
    c_1 * persistence(C)
  + c_2 * spatial_overlap(C)
  + c_3 * direction_consistency(C)
  + c_4 * external_anomaly_mass(C)
  + c_5 * SNR_struct(C)
```

当：

```text
Precision(C) * Momentum_Xi(C) > I_P(τ)
```

则注意力应该优先转向反证链覆盖区域，或生成 masking/replay 提案。

### 5.5 屏蔽收益

屏蔽不是删除，而是测试：如果暂时压低一个区域的注意力，系统的总账是否变好？

```text
MaskingBenefit(S) =
    released_compute_budget(S)
  + hidden_R_exposure(S)
  + Xi_clarification_gain(S)
  - P_damage_risk(S)
```

只有当 `MaskingBenefit > 0` 且 `P_damage_risk` 可控时，masking proposal 才能进入 sandbox。

---

## 6. 外部熵正本路径积分

### 6.1 路径定义

注意力路径 `Γ` 是一组窗口与区域的序列：

```text
Γ = [(r_0,w_0), (r_1,w_1), ..., (r_k,w_k)]
```

路径类型包括：

```text
ATTENTIONAL          注意力从一个区域转移到另一区域
MACRONODE            宏观节点候选随时间演化
BOUNDARY_LEAKAGE     粘合边界上的外溢信息流
RESIDUAL             Xi / anomaly 残余沿时间累积
MASKING              屏蔽提案执行路径
```

### 6.2 路径积分基本式

对路径 `Γ`：

```text
I_ledger(Γ) = Σ_i [
    λ_F * |ΔF_ext(i)|
  + λ_D * D(i)
  + λ_N * N(i)
  + λ_A * A_ext(i)
  + λ_G * NoetherViolation(i)
]
```

其中：

```text
ΔF_ext(i) = F_ext(w_{i+1}) - F_ext(w_i) - W_ext(i)
```

这表示路径每段的外部自由能账变化，在扣除合法源项后的账本成本。

### 6.3 SNR 修正

路径积分不能孤立解释。需要结构性信噪比修正：

```text
SNR_path(Γ) =
  StructuredResidualMass(Γ)
  /
  [NoiseBudget(Γ) + NumericalDissipation(Γ) + eps]
```

最终解释使用：

```text
I_interpreted(Γ) = I_ledger(Γ) / [1 + η * SNR_path(Γ)]
```

直觉：

- 如果路径上残差高但结构性也高，不应简单判为失败。
- 如果路径上残差高且 SNR 低，则更可能是噪声劫持或数值伪影。

### 6.4 Meta-proxy 灵敏度修正

继承 v34.1，对路径积分加入元参数灵敏度风险：

```text
I_corrected(Γ) = I_ledger(Γ) * [1 + μ * Σ_j |∂I_ledger / ∂θ_j|]
```

其中 `θ_j` 是外部熵账本的 meta-proxy 参数，例如：

```text
κ_I, τ, α_tr, α_res, β_bd, noether_threshold, noise_weight
```

禁止解释：

```text
I_corrected 最小化 ≠ truth
I_corrected 低 ≠ biological validity
I_corrected 高 ≠ 一定错误
```

### 6.5 Boltzmann-style 选择器

如果多个注意力路径候选同时存在，可以定义候选权重：

```text
Prob(Γ_i) = exp[-I_corrected(Γ_i)/β] / Σ_j exp[-I_corrected(Γ_j)/β]
```

它只用于 proposal ranking，不用于科学结论。

### 6.6 边界泄漏积分

对粘合边界 `∂M`：

```text
Leakage(∂M) = ∮_{∂M} J_entropy · dl
```

离散实现：

```text
Leakage(∂M) ≈ Σ_edges crossing boundary entropy_flux(edge)
```

解释：边界泄漏高说明现有粘合结构不能吸收外部信息流，需要把注意力投向边界外溢区域。

---

## 7. 数据模型设计

### 7.1 `v35_run_manifest`

| 字段 | 类型 | 说明 |
|---|---|---|
| run_id | text | v35 run id |
| version | text | `v35_attentional_path_integral_governance` |
| base_version | text | v34.1 |
| governance_mode | text | light / standard / full audit |
| attention_sandbox_only | integer | 必须为 1 |
| path_integral_audit_enabled | integer | 必须为 1 |
| source_facts_rewritten | integer | 必须为 0 |
| hot_swap_allowed | integer | 必须为 0 |
| real_action_authorized | integer | 必须为 0 |
| created_at | text | 生成时间 |

### 7.2 `v35_attention_region_index`

统一记录候选注意力区域。

| 字段 | 说明 |
|---|---|
| region_id | 区域 ID |
| region_type | confirmed_p / r_counter / xi_residual / anomaly / macro_node / bottom_prediction / boundary |
| source_version | v25-v34 来源 |
| source_ref | 上游对象引用 |
| window_start / window_end | 时间范围 |
| support_domain_ref | 支撑域 |
| coordinate_summary | 坐标摘要 |
| scale_contract_ref | v32 scale contract |
| proxy_provenance_ref | proxy 身份 |

### 7.3 `v35_attention_tension_map`

| 字段 | 说明 |
|---|---|
| tension_id | ID |
| region_id | 候选区域 |
| P_mass | confirmed P 质量 |
| R_counter_mass | R 反证质量 |
| Xi_residual_mass | Xi 残余质量 |
| anomaly_mass | anomaly 质量 |
| masking_exposure | masking 后暴露程度 |
| boredom_decay | 稳定区域衰减 |
| compute_cost | 计算成本 |
| attention_tension | 综合张力 |
| tension_rank | 排名 |
| formula_ref | 计算 recipe |

### 7.4 `v35_p_inertia_profile`

| 字段 | 说明 |
|---|---|
| inertia_id | ID |
| p_ref | confirmed P 或 macro node |
| duration | 持续时间 |
| internal_coherence | 内部相干性 |
| repeated_confirmation_count | 重复确认次数 |
| low_divergence_history | 低散度历史 |
| inertia_score | P 惯性 |
| shielding_allowed | 是否允许生成屏蔽边界 |

### 7.5 `v35_r_counter_chain`

| 字段 | 说明 |
|---|---|
| chain_id | 反证链 ID |
| r_refs | R counter refs |
| window_span | 跨窗口范围 |
| persistence | 持续性 |
| spatial_overlap | 空间重合 |
| direction_consistency | 方向一致性 |
| external_anomaly_mass | 外部异常质量 |
| xi_support_refs | Xi 支撑 |
| counter_momentum | 反证链动量 |

### 7.6 `v35_xi_momentum_chain`

| 字段 | 说明 |
|---|---|
| xi_chain_id | Xi 链 ID |
| xi_refs | Xi surface refs |
| residual_mass | 残余质量 |
| persistence | 持续性 |
| snr_struct | 结构性信噪比 |
| candidate_status | noise / novelty / unresolved |
| eligible_for_attention | 是否可生成注意力 |

### 7.7 `v35_masking_proposal`

| 字段 | 说明 |
|---|---|
| masking_id | ID |
| target_region_ref | 屏蔽目标 |
| masking_type | IGNORE / SUPPRESS / HOLD / REPLAY_WITH_MASK |
| rationale_ref | 驱动源 |
| proposed_duration | 持续窗口 |
| expected_effect | 预期效果 |
| sandbox_only | 必须为 1 |
| data_deletion_allowed | 必须为 0 |
| status | proposed / running / completed / reverted |

### 7.8 `v35_attention_proposal`

| 字段 | 说明 |
|---|---|
| proposal_id | ID |
| proposal_type | INCREASE_RESOLUTION / REDUCE_RESOLUTION / SHIFT_FOCUS / INITIATE_MASKING / DEEPEN_PRECISION |
| target_region_ref | 目标区域 |
| rationale_source | tension / anomaly / R chain / Xi chain / masking |
| proposed_intensity | 强度 |
| duration_budget_windows | 持续窗数 |
| expected_compute_cost | 计算成本 |
| proxy_provenance_id | proxy 身份 |
| sandbox_only | 必须为 1 |
| real_action_authorized | 必须为 0 |
| status | proposed / approved / running / completed / rejected |

### 7.9 `v35_attention_transition_log`

| 字段 | 说明 |
|---|---|
| transition_id | ID |
| from_region_ref | 起点 |
| to_region_ref | 终点 |
| from_proposal_id | 来源提案 |
| to_proposal_id | 目标提案 |
| trigger | 转移原因 |
| window_span | 时间跨度 |
| governance_mode | 治理模式 |

### 7.10 `v35_attentional_path_integral_audit`

| 字段 | 说明 |
|---|---|
| path_integral_id | ID |
| path_type | ATTENTIONAL / MACRONODE / BOUNDARY_LEAKAGE / RESIDUAL / MASKING |
| path_definition_json | 路径定义 |
| integrated_delta_F_ext | Σ ΔF_ext |
| integrated_dissipation | Σ D |
| integrated_noise | Σ N |
| integrated_anomaly_mass | Σ A |
| noether_violation_cost | Noether violation 总成本 |
| mean_SNR_path | 平均路径 SNR |
| corrected_integral | SNR 与 meta-proxy 修正后积分 |
| source_balance_ids | 外部账本窗口引用 |
| conclusion | STABLE_ATTRACTOR / NOISE_EXPLORATION / NOVELTY_EMERGING / RESOURCE_LEAK / ATTENTION_FAILURE / HIJACKED |
| novelty_candidate | 是否新异候选 |
| forbidden_interpretation | 禁止解释 |

### 7.11 `v35_boundary_leakage_audit`

| 字段 | 说明 |
|---|---|
| leakage_id | ID |
| boundary_ref | 粘合边界 |
| boundary_type | macro_blanket / region_boundary / source_adapter_boundary |
| entropy_flux | 熵通量 |
| unexplained_flux | 未解释外溢 |
| linked_xi_refs | Xi refs |
| attention_required | 是否触发注意力 |

### 7.12 `v35_attention_performance_report`

| 字段 | 说明 |
|---|---|
| report_id | ID |
| proposal_id | 注意力提案 |
| path_integral_id | 路径积分审计 |
| delta_F_attn | 注意力路径自由能变化 |
| anomaly_path_mass | 异常路径质量 |
| SNR_path | 路径信噪比 |
| persistence_gain | 新结构持续性增益 |
| Xi_change | Xi 变化 |
| compute_cost_paid | 实际成本 |
| verdict | EFFECTIVE / NEUTRAL / INEFFECTIVE / HIJACKED / NOVELTY_DISCOVERED |
| recommended_next | continue / stop / mask / replay / elevate_to_v36 |

### 7.13 `v35_guardrail_audit`

| 字段 | 说明 |
|---|---|
| guard_id | ID |
| rule | 检查规则 |
| status | PASS / FAIL / WARN |
| target_ref | 被检查对象 |
| details | 说明 |

### 7.14 `v35_acceptance_report`

| 字段 | 说明 |
|---|---|
| check_id | ID |
| status | PASS / FAIL / WARN |
| blocking | 是否阻断 |
| details | 说明 |

---

## 8. Runtime sidecar 设计

SQLite 只存索引、摘要、结果和审计账。高频路径、窗口序列、区域集合应进入 runtime sidecar。

```text
runtime_store/v35/
  attention_region_index_v35.jsonl
  attention_tension_map_v35.jsonl
  p_inertia_profile_v35.jsonl
  r_counter_chain_v35.jsonl
  xi_momentum_chain_v35.jsonl
  masking_proposal_v35.jsonl
  attention_proposal_v35.jsonl
  attention_transition_log_v35.jsonl
  attentional_path_integral_audit_v35.jsonl
  boundary_leakage_audit_v35.jsonl
  attention_performance_report_v35.jsonl
  guardrail_events_v35.jsonl
  runtime_manifest_v35.json
```

大对象，如完整路径序列或区域支持域点集，应只在 sidecar 中保存，SQLite 保存 digest / path / row count / sha256。

---

## 9. 核心算法流程

### 9.1 构建候选注意力区域

```text
for each upstream object in v25-v34:
    if object is confirmed_P / R_counter / Xi / anomaly / macro_node / bottom_prediction:
        normalize into attention_region_index
        bind source_ref, proxy_ref, scale_contract_ref
```

### 9.2 计算注意力张力

```text
for each region r:
    collect P_mass, R_mass, Xi_mass, anomaly_mass, masking_exposure
    compute boredom_decay and compute_cost
    T_attn = weighted sum
    rank regions by T_attn
```

### 9.3 生成注意力提案

```text
for top-ranked regions:
    if driven by P inertia:
        proposal_type = MAINTAIN / REDUCE_RESOLUTION
    if driven by R or Xi:
        proposal_type = SHIFT_FOCUS / DEEPEN_PRECISION
    if driven by masking benefit:
        proposal_type = INITIATE_MASKING
    create attention_proposal with sandbox_only=1
```

### 9.4 生成反证链与 Xi 动量链

```text
for each R/Xi residual group:
    compute persistence, spatial overlap, direction consistency
    compute counter_momentum / xi_momentum
    if Precision * Momentum > P inertia:
        mark eligible_for_attention
```

### 9.5 沙盒模拟注意力转移

```text
for each proposal:
    simulate attention allocation for duration_budget_windows
    do not modify source facts
    do not modify P/R/Xi labels
    record transition log
```

### 9.6 外部熵正本路径积分

```text
for each attention path Γ:
    collect F_ext, D, N, A_ext, Noether violation from v34/v34.1
    compute I_ledger(Γ)
    compute SNR_path(Γ)
    compute I_corrected(Γ)
    classify conclusion
```

### 9.7 生成绩效报告

```text
if I_corrected low and SNR moderate/high:
    verdict = EFFECTIVE or STABLE_ATTRACTOR
elif anomaly path high and SNR high:
    verdict = NOVELTY_DISCOVERED
elif I_corrected high and SNR low:
    verdict = HIJACKED or INEFFECTIVE
else:
    verdict = NEUTRAL
```

### 9.8 Guardrail 检查

```text
assert source_facts_rewritten == 0
assert real_action_authorized == 0
assert attention_sandbox_only == 1
assert path_integral_not_truth_objective == 1
assert no proposal writes mainline P/R/Xi
```

---

## 10. Governance mode

v35 继承 v34.1 的 governance mode，但注意力层有独立开销。

| 模式 | 使用场景 | 审计深度 |
|---|---|---|
| light_diagnostic | 快速调试 | 只计算 top-k attention tension，不全量 path integral |
| standard_governance | 默认 | top-k proposal + path integral + SNR |
| full_audit | 晋升或异常复核 | 全量 attention path + boundary leakage + meta-proxy sensitivity |
| calibration_run | 调参数 | 只校准权重，不写结论 |
| scientific_candidate | 未来 | 仍需人工/外部证据，不自动开启 |

---

## 11. Acceptance 标准

### 11.1 基础门

```text
1. v35_run_manifest 存在。
2. source_facts_rewritten = 0。
3. real_action_authorized = 0。
4. attention_sandbox_only = 1。
5. path_integral_audit_enabled = 1。
```

### 11.2 注意力门

```text
1. attention_region_index count > 0。
2. attention_tension_map count > 0。
3. 每个 attention_proposal 必须有 rationale_source。
4. 每个 proposal 必须绑定 proxy_provenance_id。
5. proposal 不能直接写 P/R/Xi。
```

### 11.3 路径积分门

```text
1. 每个 completed proposal 必须有 path_integral_audit。
2. path_integral 源数据必须来自 external entropy ledger。
3. conclusion 不得标记为 scientific truth。
4. I_corrected 不能被作为 truth loss。
5. high anomaly + high SNR 必须可进入 novelty candidate 或 Xi review。
```

### 11.4 屏蔽门

```text
1. masking proposal 不得删除数据。
2. masking 必须有持续窗口上限。
3. masking 结束后必须生成 performance report。
4. masking 不能永久压制高 SNR persistent anomaly。
```

### 11.5 边界门

```text
1. hot_swap_allowed = 0。
2. external_ledger_can_write_mainline = 0。
3. Xi direct-to-P/R = 0。
4. macro-node direct promotion = 0。
```

---

## 12. 风险清单

| 风险 | 描述 | v35 对策 |
|---|---|---|
| 注意力劫持 | 噪声区域抢占注意力 | SNR path + anomaly persistence |
| P 独占 | 稳定 P 永远获得资源 | boredom decay |
| R 过拟合 | R 反证链把正常误差当结构 | persistence + spatial overlap + Noether audit |
| Masking 越权 | 屏蔽变成删除或永久忽略 | sandbox_only + duration limit + restore audit |
| 路径积分硬化 | 积分低被当真理 | forbidden interpretation |
| 计算过载 | 全量 attention path 爆炸 | governance mode + top-k |
| ledger 残差诱惑 | 试图把残差归零 | SNR-first interpretation |
| external ledger 越权 | 账本写主链 | read-only ledger binding |

---

## 13. 与 v36-v40 的衔接

### 13.1 v36 Macro Renormalization / Markov Blanket

v35 输出：

```text
high-performing attention regions
persistent boundary leakage
high inertia P/R trajectories
novelty-discovered residual paths
```

v36 使用这些对象生成：

```text
macro blanket candidate
coarse-grained node
shielding boundary
cross-scale transition map
```

### 13.2 v37 Tensor / Zarr Runtime Backend

v35 仍可用 SQLite + JSONL sidecar 做 diagnostic 实现。但如果 attention path 数量增长，v37 必须将高频路径积分迁移到 tensor / Zarr。

### 13.3 v38 Policy Coupling

v35 的 attention performance report 可以成为 v38 policy learning 的 prior：

```text
policy should first act where attention has repeatedly discovered high-SNR novelty
```

### 13.4 v40 Scientific Boundary Audit

v35 所有 attention verdict 仍是 proxy-derived。只有经过多源真实数据、控制实验、外部复现，才允许进入 scientific candidate。

---

## 14. 施工优先级

### Phase 1：Schema-only diagnostic

```text
实现 v35_run_manifest
实现 attention_region_index
实现 tension_map
实现 attention_proposal
实现 path_integral_audit
实现 acceptance
```

### Phase 2：SNR + masking

```text
实现 R/Xi chains
实现 masking proposal
实现 SNR path interpretation
实现 boundary leakage audit
```

### Phase 3：性能与治理

```text
实现 governance mode
实现 top-k attention path
实现 cost audit
实现 report and query CLI
```

### Phase 4：准备 v36

```text
将 high-performing attention paths 输出为 macro-renormalization candidates
```

---

## 15. 一句话结论

v35 的本质不是让系统更聪明，而是让系统第一次拥有 **受外部正本审计的选择性观察能力**。

它让 Morphosphere 从：

```text
被动记录 evidence
被动审判 shadow
被动保存 Xi
```

推进为：

```text
主动提出注意力提案
主动测试屏蔽与反证链
主动追踪粘合外流动的信息
但每一次主动选择都必须接受外部熵正本的路径积分审计
```

最终边界：

```text
Attention is a sandboxed, proxy-tagged, ledger-audited proposal.
It is not truth, not action, not biology, and not authority.
```
