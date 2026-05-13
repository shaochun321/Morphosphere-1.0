# Morphosphere v34.1 蓝图：Meta-Proxy Governance + Runtime Guard Hardening

版本定位：v34.1 `meta_proxy_runtime_guard_hardening`。

交付性质：施工蓝图，不是代码实现。目标是在 v34 Proxy × External Entropy Control Plane 之后，补全“治理自身的治理”与“执行层硬约束”，避免 proxy 控制平面、外部熵账本、Noether 审计、可微子图本身演化成新的越权中心。

核心判断：v34 管住了业务 proxy；v34.1 要管住 proxy 治理系统本身。

## 0. 蓝图摘要

v34 已经建立两条治理线：Proxy Control Plane 负责“什么有资格被解释”，External Entropy Ledger Plane 负责“解释造成的等效能量、耗散、噪声、异常差额去了哪里”。v34.1 不新增新的认知层，也不替代 v34；它是 v34 的硬化版本。

```text
v34 已有：
  proxy registry
  proxy dependency edge
  proxy propagation path
  proxy drift audit
  equivalent energy ledger
  dissipation / noise / anomaly ledger
  Noether-style balance audit
  differentiable proxy subgraph

v34.1 追加：
  ledger meta-proxy registry
  proxy parameter dependency
  amplification / sensitivity audit
  structured signal-to-noise ledger interpretation
  runtime guard rules
  gradient path audit
  forbidden loss / name / write audit
  governance mode profile
  scientific transition ladder
  runtime/ledger cost audit
```

## 1. 为什么需要 v34.1

v34 的设计非常强，但也产生了新的风险：当一个治理系统足够复杂时，它自身也会变成 proxy。外部熵账本中的 κ_I、τ、α、β、Noether 阈值、账本残差分类规则，本质上都不是自然真理，而是带假设的治理参数。如果这些参数不被登记、审计和替换，它们会成为新的概念漂移源。

外部分析指出 v34 的核心价值在于“问责”：通过 `v34_proxy_entropy_binding` 把 proxy 结果与等效能量、耗散、噪声、异常和对称性审计挂钩；但同时警告不要把 ledger residual 当作全局优化目标，异常残差可能是 novelty 的数学指纹，而不是必须被抹平的错误。

另一个分析指出 v34 是优秀的一阶治理框架，但缺少“元治理”：账本参数自身的 proxy 治理、可微化的 runtime 硬阻断、守恒解释权的客观化、治理成本收益阈值和 scientific transition ladder。

因此 v34.1 的任务不是加强控制欲，而是给控制系统本身戴上标签、限权、监控和退出条件。

## 2. 哲学边界：治理不是新本体

- Proxy 不是造假，而是带身份证的脚手架；但 proxy registry 本身也不是神谕。
- External Entropy Ledger 是外部数学正本，但它记录的是 ledger energy / effective energy / free-energy-like quantity，不是项目对象携带焦耳意义的物理能量。
- Noether-style audit 是对称性防错器，不是证明系统遵循真实物理定律。
- Differentiable proxy subgraph 是灵敏度和一致性工具，不是 truth optimizer。
- Governance mode 是运行约束，不是科学认证。

```text
禁止解释：
  ledger_residual_minimized != scientific_truth
  proxy_consistency_loss != biological_fitness
  noether_audit_pass != physical_law_verified
  macro_node_candidate != causal_real_entity
  action_sandbox_success != real_action_authorization
```

## 3. 数学基础：从 proxy 到 meta-proxy

### 3.1 Proxy 构造

```text
目标对象：       X*
可用代理：       X_hat = π_θ(E, A, M)

E = Evidence，可观测证据
A = Assumptions，显式假设
M = Model / mechanism，构造模型
θ = 参数、阈值、窗口、权重、核函数等
```

v34 主要治理 X_hat。v34.1 进一步治理 θ，因为 θ 往往是 ledger、precision、divergence、Noether audit 的实际权力来源。

### 3.2 Meta-proxy

```text
meta_proxy θ_j:
  θ_j ∈ {κ_I, τ, α_tr, α_cl, α_org, α_res,
         β_cg, β_bd, β_num,
         noise weights,
         Noether thresholds,
         precision weights,
         governance-mode budgets}

θ_j 的合法性来自：
  explicit tag
  parameter source
  calibration status
  allowed run type
  replacement condition
  forbidden interpretation
```

### 3.3 Proxy 传播

```text
若：
  Y = f(X_hat, θ)
  Z = g(Y, φ)

则：
  Z 不是单纯的 downstream result，
  而是 proxy-derived result with propagation path:

  X_hat -> Y -> Z
  θ -> Y
  φ -> Z
```

因此 v34.1 必须记录 `proxy_propagation_path` 的参数依赖，而不仅是结果依赖。

### 3.4 放大系数与漂移风险

```text
局部灵敏度：
  a_i = || ∂y_i / ∂x_i || 或离散近似 Δy_i / Δx_i

路径放大：
  A_path = Π_i max(a_i, ε)

对数形式：
  log A_path = Σ_i log max(a_i, ε)

风险解释：
  A_path >> 1   proxy drift 可能被放大
  A_path ≈ 1    近似线性传递
  A_path << 1   下游对该 proxy 不敏感
```

离散图结构中不一定存在严格导数，因此 v34.1 支持两类灵敏度：连续子图用 autograd；离散拓扑用 finite-difference / perturbation sensitivity。

## 4. 外部熵账本的元治理

### 4.1 外部账本公式

```text
外部信息等效能量：
  E_info = κ_I I

结构势：
  U_struct(m) = λ_bw BW_m + λ_con C_m + λ_frag F_m + λ_bnd B_m + λ_tr T_m

外部自由能账：
  F_ext(m) = U_struct(m) - τ H_ext(m)

外部总平衡：
  F_ext(m+1) - F_ext(m) = W_ext(m) + N(m) - D(m) - A(m)
```

v34.1 的关键修正：这套公式本身是 ledger-level proxy。它不是自然定律本身，而是用于记录、分类和审计的外部数学账本。

### 4.2 账本残差不是敌人

```text
balance_residual(m) =
  ΔF_ext(m) - W_ext(m) - N(m) + D(m) + A(m)

错误用法：
  minimize Σ balance_residual^2 as truth objective

正确用法：
  classify residual:
    unstructured_noise
    numerical_artifact
    source_missing
    structured_anomaly
    persistent_novelty
    candidate_emergence
```

外部账本不是为了把所有残差归零，而是为了区分无结构噪声与结构性异常。持续、局部一致、跨窗口稳定的残差，可能是 Xi 或 emergence 的材料。

### 4.3 信噪比优先解释

```text
SNR_struct(m) =
  [persistence(m) * support_coherence(m) * entropy_closure_quality(m)]
  / [noise_budget(m) + numerical_dissipation(m) + ε]

interpretation:
  high SNR + high residual -> structured anomaly / Xi candidate
  low SNR + high residual  -> noise / low confidence
  high SNR + low residual  -> stable confirmed accounting
  low SNR + low residual   -> low-impact region
```

v34.1 不把残差大小当成唯一风险，而把结构性信噪比作为外部熵账本解释的核心指标。

## 5. Runtime 硬阻断：从纸面约束到代码级边界

v34 中已经声明 differentiable subgraph 不得越权。v34.1 要把这变成 runtime guard，而不是文档约束。

```text
硬规则：
  source facts must be frozen/detached
  evidence tables cannot be mutated by differentiable subgraph
  mainline P/R/Xi cannot be written by optimizer
  external ledger cannot write source facts
  loss names cannot include truth / biological_fitness / real_physics unless certified
  trainable parameters must be explicitly allowlisted
  forbidden parameters must be blocked at runtime
  gradient path must be auditable
```

### 5.1 可微子图边界

```text
允许优化：
  proxy consistency parameters
  window smoothing weights
  non-source precision weights
  sandbox-only calibration parameters
  differentiable surrogate kernels

禁止优化：
  raw evidence points
  source hash / provenance
  source facts
  P/R/Xi truth labels
  scientific run flags
  real action authorization flags
  external ledger authoritative records
```

### 5.2 离散拓扑的处理

外部批判指出：Morphosphere 的核心底座包含大量离散图拓扑，直接 autograd 会遇到不可导断裂。因此 v34.1 不把所有 proxy dependency graph 都变成可微图。

```text
连续可微路径：
  coordinate normalization
  weight / precision / smoothing kernel
  proxy consistency score
  ledger residual proxy

离散非可微路径：
  graph edge existence
  threshold gate
  Xi reentry policy
  acceptance gate
  source fact freeze
  scientific promotion block

处理方式：
  continuous path -> autograd / sensitivity
  discrete path   -> finite difference / control experiment / audit rule
```

## 6. Governance Mode：不同阶段不同负担

v34.1 必须避免“治理锁死”。不同 run 类型应使用不同审计深度。

| Mode | 目的 | Proxy 容忍度 | Ledger 审计 | Runtime 要求 |
| --- | --- | --- | --- | --- |
| light_diagnostic | 快速开发/调试 | 高 | 摘要级 | 轻量 sidecar |
| standard_governance | 默认工程运行 | 中 | 窗口级平衡 | 关键路径 audit |
| full_audit | 版本验收/发布前 | 低 | 完整 proxy+ledger 绑定 | 完整 runtime guard |
| calibration_run | 参数校准 | 很低 | meta-proxy 记录必需 | 可微子图 guard 必需 |
| scientific_candidate | 科学候选 | 极低 | 多源外部验证必需 | 禁止未替换 critical proxy |

## 7. v34.1 建议新增 schema

| 表名 | 作用 | 关键字段 |
| --- | --- | --- |
| v341_run_manifest | 记录 v34.1 运行边界 | run_id, base_version, governance_mode, source_facts_rewritten=0 |
| v341_ledger_meta_proxy_registry | 登记外部账本参数自身的 proxy 身份 | meta_proxy_id, parameter_name, proxy_type, replacement_condition, forbidden_interpretation |
| v341_proxy_parameter_dependency | 记录结果对 proxy 参数的依赖 | result_ref, parameter_proxy_ref, dependency_role, dependency_strength |
| v341_proxy_result_lineage | 跨表记录 proxy-derived 结果血缘 | result_id, upstream_proxy_refs, propagation_path, downstream_table |
| v341_proxy_amplification_audit | 审计 proxy 漂移放大风险 | path_id, local_gain, log_path_gain, risk_class |
| v341_snr_ledger_interpretation | 用结构性信噪比解释残差 | window_id, residual, snr_struct, residual_class |
| v341_runtime_guard_rule | 代码级硬阻断规则登记 | rule_id, target, enforcement_mode, failure_policy |
| v341_gradient_path_audit | 审计可微子图梯度路径 | subgraph_id, source_facts_detached, forbidden_path_count |
| v341_forbidden_loss_name_audit | 拦截误导性 loss 命名 | loss_name, status, reason |
| v341_governance_mode_profile | 不同运行模式的治理预算 | mode, proxy_density_budget, ledger_depth, runtime_audit_depth |
| v341_scientific_transition_ladder | 定义 proxy 到 scientific candidate 的晋升路径 | object_ref, current_level, required_evidence, promotion_status |
| v341_runtime_ledger_cost_audit | 审计治理成本与 IO 开销 | table_ref, row_count, sidecar_size, serialization_cost_proxy |
| v341_acceptance_report | 验收结果 | check_id, status, details |

## 8. Runtime sidecar 设计

```text
runtime_store/v341/
  meta_proxy_registry_v341.jsonl
  proxy_parameter_dependency_v341.jsonl
  proxy_amplification_audit_v341.jsonl
  snr_ledger_interpretation_v341.jsonl
  gradient_path_audit_v341.jsonl
  runtime_guard_events_v341.jsonl
  governance_mode_profile_v341.jsonl
  runtime_ledger_cost_audit_v341.jsonl
```

SQLite 仍只作为 ledger/index/manifest/acceptance，不承载高频 runtime 计算。高频 path-level audit、gradient trace、cost profiling 应进入 runtime_store。

## 9. 核心算法流程

### 9.1 账本元参数登记

```text
for each ledger parameter θ:
    register θ as meta_proxy
    record source, default, formula context
    record allowed run types
    record replacement condition
    record forbidden interpretation
```

### 9.2 Proxy 传播路径扩展

```text
for each proxy-derived result r:
    upstream = collect proxy inputs + meta-proxy parameters
    path = trace table lineage and runtime refs
    classify criticality
    store v341_proxy_result_lineage
```

### 9.3 放大审计

```text
for each propagation path:
    if continuous path:
        estimate local gain by autograd or local sensitivity
    else:
        estimate by finite-difference control perturbation
    compute log_path_gain
    assign risk_class = low / medium / high / explosive
```

### 9.4 SNR-first 账本解释

```text
for each balance window:
    residual = ΔF_ext - W - N + D + A
    snr_struct = persistence * support_coherence * closure_quality / (noise + numerical_dissipation + ε)
    classify residual into:
        noise
        numerical_artifact
        missing_source
        structured_anomaly
        persistent_novelty
        emergence_candidate
```

### 9.5 Runtime guard 执行

```text
before running differentiable subgraph:
    verify source_facts detached
    verify trainable params allowlisted
    verify forbidden params blocked
    verify loss names legal
    verify no write path to mainline/source tables
    emit gradient_path_audit

on violation:
    block run
    write runtime_guard_event
    mark acceptance fail
```

## 10. 与 v34 的关系

```text
v34:
  管业务 proxy 与外部熵账本的绑定

v34.1:
  管 ledger 参数、可微子图、治理模式、runtime guard 和科学晋升边界

v34 关注：
  proxy result -> ledger consequence

v34.1 关注：
  governance rule -> meta-proxy status -> runtime enforceability
```

## 11. Acceptance 标准

- 所有外部账本核心参数必须在 `v341_ledger_meta_proxy_registry` 中登记。
- 每个 weighted divergence / free-energy proxy / macro-node candidate 必须保留 proxy propagation path。
- ledger residual 不得被命名或用作 truth objective。
- 可微子图必须证明 source facts detached / frozen。
- 禁止 loss 名称：truth_loss、biological_fitness、physical_truth_loss、real_free_energy_loss。
- persistent structured residual 不得被自动归零，必须允许进入 Xi / emergence candidate。
- governance mode 可切换，light_diagnostic 与 full_audit 的审计深度不同。
- runtime/ledger cost audit 必须报告治理开销。
- scientific promotion 仍然默认 blocked。
- source_facts_rewritten=0、hot_swap_allowed=0、external_ledger_can_write_mainline=0。

## 12. 科学过渡阶梯

v34.1 不进入 scientific_run，但必须定义从工程 proxy 到 scientific candidate 的阶梯，避免永远停留在 proxy，又避免突然越权。

```text
Level 0: proxy registered
Level 1: proxy + ledger binding complete
Level 2: propagation path and meta-proxy dependencies recorded
Level 3: control experiments passed
Level 4: multisource evidence support
Level 5: external physical validation candidate
Level 6: scientific_candidate gate review
Level 7: scientific_run allowed only after critical proxy replacement
```

## 13. 风险清单

| 风险 | 描述 | v34.1 对策 |
| --- | --- | --- |
| 账本硬化 | 外部熵账本参数被误当自然真理 | ledger meta-proxy registry |
| 残差诱惑 | 把 residual 最小化当 truth objective | SNR-first interpretation + forbidden loss audit |
| Proxy 高塔 | 多层 proxy 误差被非线性放大 | amplification audit |
| 可微越权 | 梯度路径间接影响 source facts | runtime guard + gradient path audit |
| 离散不可导 | 图拓扑无法被连续梯度直接优化 | finite difference / control audit |
| 治理过载 | 审计成本超过收益 | governance mode + cost audit |
| 科学边界漂移 | engineering proxy 被宣传成科学对象 | scientific transition ladder + promotion block |

## 14. 与后续版本关系

```text
v34.1 -> v35:
  先加固 proxy/ledger 元治理，再进入 runtime tensor/graph backend。

v34.1 -> v36:
  bottom prediction vs evidence trial 必须使用 v34.1 的 propagation/amplification/SNR 审计。

v34.1 -> v37:
  policy learning 的 expected free-energy proxy 必须携带 meta-proxy 和 ledger balance refs。

v34.1 -> v40:
  scientific boundary audit 以 v34.1 的 scientific transition ladder 为前置条件。
```

## 15. 一句话结论

v34 建立了 proxy 与外部熵账本的问责制；v34.1 建立问责制自身的问责制。它不是新的世界模型，而是防止治理系统本身变成黑箱权力中心的元治理层。
