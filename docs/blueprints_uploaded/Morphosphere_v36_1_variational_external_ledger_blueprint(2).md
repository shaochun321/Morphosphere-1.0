# Morphosphere v36.1 蓝图：外部账本变分泛函与能量—信息测度求解

**版本定位**：`v36_1_variational_external_ledger_measure`

**交付性质**：施工蓝图，不是工程实现。

**核心修正**：上一版 v36 用“差分 Xin”作为稳态耗散源周围的局部变化代理。现在修正为：不再把 Xin 首先理解为点态差分，而是把它提升为**外部熵账本约束下的变分残差 / Euler-Lagrange defect / action residual field**。差分 Xin 只作为最小 fallback，不再是主数学对象。

---

## 0. 直接结论

你的判断是对的：如果项目已经进入“外部账本中的能量—信息测度与信息时空轨关系”的层次，那么仅做

```text
Delta Xin = Xin(t+1) - Xin(t)
```

确实太局部。它只能捕捉窗口间变化，不能解释为什么这条信息时空轨、这个耗散源、这组 P/R/Xi 递归链在外部账本中构成一种稳定或不稳定的测度结构。

更合适的数学对象是：

```text
外部账本约束下的作用量泛函 / 能量—信息变分泛函
```

也就是：

```text
S_IE[Gamma]
```

其中 `Gamma` 不是普通几何路径，而是由 T/O/P/R/Xin 递归链、注意力路径、超边 incidence、外部账本窗口共同定义的信息时空轨。

Xin 的位置应从：

```text
局部残余差分
```

升级为：

```text
变分不闭合残差
```

也就是：

```text
Xin_var = Euler-Lagrange residual / stationarity defect / ledger-constrained action defect
```

一句话：

> **差分 Xin 问“局部变了多少”；变分 Xin 问“这条信息—能量路径为什么不是稳定作用量路径”。**

---

## 1. 为什么差分 Xin 不够

### 1.1 差分 Xin 的能力边界

差分 Xin 可以表达：

```text
某个窗口到下一个窗口，Xi 质量、残余分布、异常质量、局部测度发生了多少变化。
```

它适合做：

```text
局部扰动检测
窗口级 anomaly change
短程 residual tracking
局部曲率 proxy 的输入项
```

但它不能回答：

```text
这条信息时空轨是否是外部账本下的低作用量路径？
某个稳态耗散源是否真的支撑了一个测度域？
相对运动 / 相对静止是否来自路径变分稳定性？
某个 Xin 是噪声、局部涨落，还是全局作用量不闭合？
```

### 1.2 项目当前真正需要的对象

当前项目需要的是一个跨窗口、跨路径、跨账本的对象：

```text
Gamma = {z_0, z_1, ..., z_K}
```

其中：

```text
z_m = (T_m, O_m, P_m, R_m, Xin_m, A_m, H_m, ledger_m)
```

然后问：

```text
这条 Gamma 在外部账本中是否接近一个稳定作用量路径？
```

这不是差分问题，而是变分问题。

---

## 2. 原哲学—数学构想如何降级 / 最小化 / 修正为工程对象

从此版本起，本章节应成为所有蓝图的固定章节。

| 原哲学—数学构想 | 不能直接采用的原因 | 降级后的工程对象 | 最小化 / 修正机制 | 禁止解释 |
|---|---|---|---|---|
| 真实物理作用量 | 项目没有完整物理哈密顿量、真实力场和连续相空间 | `S_IE_proxy[Gamma]` 外部账本作用量代理 | 在候选路径间做 action ranking / stationarity scoring | `S_IE` 不是真实物理作用量 |
| 连续变分原理 `delta S = 0` | T/O/P/R/Xin 是离散窗口、图、超边和账本事件 | 离散变分残差 `EL_residual_m` | 对窗口路径求离散 Euler-Lagrange residual | `EL_residual=0` 不是科学真理 |
| 微分 Xin 场 | 当前无连续可微场和真实坐标流形 | `Xin_var` 变分缺陷场 | 由 action residual、ledger residual、constraint residual 共同定义 | `Xin_var` 不是物理场 |
| 信息—能量度规 | 外部账本能量仍是 ledger-unit / proxy | `mu_IE` provisional variational metric proxy | 用外部账本平衡和坐标锚约束 | 不是真实时空度规 |
| 最小作用量路径 | 不可全局求解，路径空间巨大 | top-k candidate path scoring / beam search / Dijkstra on hyperedges | 在局部 confirmed hyperedge neighborhood 内近似 | 最小路径不是 truth |
| 外部熵正本作为宇宙正本 | 账本参数自身是 meta-proxy | read-only ledger constraint surface | 用 augmented Lagrangian 约束，不反写主线 | 账本不能写 P/R/Xi |
| 语义“运动/静止” | 语义标签不能从测度中自封 | `relation_readout_proxy` | 只读投影，不写 semantic label | 相对运动 proxy ≠ 真实运动标签 |

这一降级原则的核心是：

> **让数学成为工程的约束形状，而不是让工程冒充数学的完全实现。**

---

## 3. 核心数学对象

### 3.1 信息时空轨 Gamma

定义一条信息时空轨：

```text
Gamma = (z_0 -> z_1 -> ... -> z_K)
```

每个状态：

```text
z_m = {
  T_m: latent trajectory / trace window,
  O_m: object candidate or support domain,
  P_m: positive spacetime measure,
  R_m: counter-measure / challenger chain,
  Xin_m: residual surface / unresolved mass,
  M_m: masking / shielding context,
  E_m: evidence refs,
  L_m: external ledger refs
}
```

Gamma 可来自：

```text
attention path
confirmed P trajectory
R-counter chain
Xi reentry path
hyperedge incidence path
macro-node lifecycle path
```

### 3.2 外部账本平衡残差

外部账本原始平衡式：

```text
F_ext(m+1) - F_ext(m) = W_ext(m) + N(m) - D(m) - A(m)
```

定义账本残差：

```text
B_m = [F_ext(m+1) - F_ext(m)] - W_ext(m) - N(m) + D(m) + A(m)
```

如果 `B_m` 大，说明该窗口的总账不闭合。它不一定是错误，可能是：

```text
unstructured noise
numerical artifact
persistent novelty
proxy drift
hidden source term
emergent structure
```

### 3.3 能量—信息拉格朗日量代理

定义离散窗口拉格朗日量代理：

```text
L_IE(z_m, z_{m+1}; theta)
```

建议最小版本：

```text
L_IE =
  lambda_track * C_track(z_m, z_{m+1})
+ lambda_ledger * B_m^2
+ lambda_diss * D_m
+ lambda_noise * N_m
+ lambda_anom * A_m_struct
+ lambda_xin * Xin_mass_m
+ lambda_r * R_counter_mass_m
+ lambda_mask * Masking_penalty_m
+ lambda_coord * Anchor_drift_m
+ lambda_noether * Noether_violation_m
+ lambda_complexity * Complexity_m
```

其中：

```text
C_track: 信息时空轨转移成本
B_m^2: 外部账本平衡残差惩罚
D_m: 耗散项
N_m: 噪声预算项
A_m_struct: 结构性异常项，不等于全部 anomaly
Xin_mass: 未闭合残余质量
R_counter_mass: 反证链挑战质量
Masking_penalty: 屏蔽层过强或过弱的惩罚
Anchor_drift: 信息—能量测度相对底层坐标锚的漂移
Noether_violation: 对称性审计破坏
Complexity: 路径复杂度 / 超边过度膨胀惩罚
```

注意：`A_m_struct` 不应全部惩罚。结构性异常可能是 novelty，应有专门通道。

### 3.4 外部账本约束的增强泛函

对整条路径：

```text
S_IE[Gamma] = sum_{m=0}^{K-1} L_IE(z_m, z_{m+1}; theta)
```

加入约束项的增强拉格朗日形式：

```text
S_tilde[Gamma, eta] =
  sum_m [
    L_base(z_m, z_{m+1})
  + eta_m * B_m
  + (kappa_B / 2) * B_m^2
  ]
```

解释：

```text
eta_m: 外部账本平衡约束的拉格朗日乘子代理
kappa_B: 平衡残差惩罚权重，必须登记为 meta-proxy
B_m: 外部账本不闭合残差
```

这不是把账本残差清零，而是让账本残差进入可解释的约束框架。

---

## 4. 变分 Xin：从 Delta Xin 到 Euler-Lagrange Defect

### 4.1 离散 Euler-Lagrange 残差

对离散路径，窗口 m 的 stationarity residual：

```text
EL_m =
  partial L_IE(z_{m-1}, z_m) / partial z_m
+ partial L_IE(z_m, z_{m+1}) / partial z_m
```

在工程上，`z_m` 不是连续张量，而是由可观测特征组成：

```text
p_mass
r_mass
xin_mass
anomaly_mass
dissipation
noise_budget
entropy_gap
masking_strength
attention_intensity
hyperedge_weight
anchor_drift
```

因此 `EL_m` 不要求真正符号求导，可通过：

```text
finite difference on approved proxy features
autograd only on allowlisted continuous parameters
control experiment on discrete topology
```

得到。

### 4.2 变分 Xin 定义

定义：

```text
Xin_var(m) = norm(EL_m) + omega_B * |B_m| + omega_C * ConstraintViolation_m
```

也可以保留向量形式：

```text
Xin_var_vector(m) = {
  EL_P_component,
  EL_R_component,
  EL_Xin_component,
  EL_ledger_component,
  EL_anchor_component,
  EL_noether_component
}
```

这样，Xin 不再只是：

```text
残余质量
```

而是：

```text
路径在外部账本变分约束下的不稳定方向。
```

### 4.3 与差分 Xin 的关系

差分 Xin 仍可保留为局部观测：

```text
Delta_Xin_m = Xin_mass(m+1) - Xin_mass(m)
```

但主判断使用：

```text
Xin_var(m)
```

关系是：

```text
Delta_Xin = 局部变化观测
Xin_var   = 变分不闭合解释
```

---

## 5. 信息—能量测度的变分定义

### 5.1 从路径作用量定义测度

对于两个区域 / 节点 / 超边簇 a,b，定义：

```text
d_IE(a,b) = inf_{Gamma: a -> b} S_IE[Gamma]
```

工程降级为：

```text
d_IE(a,b) = min over top-k admissible hyperedge paths sum L_IE(e_i)
```

其中 admissible path 必须满足：

```text
within confirmed / appealable hyperedge neighborhood
source facts read-only
external ledger read-only
Noether violation below threshold or explicitly routed to anomaly ledger
anchor drift audited
```

### 5.2 能量—信息测度密度

定义局部测度：

```text
mu_IE(e_m) = L_IE(z_m, z_{m+1}) / Delta tau_m
```

或按超边：

```text
mu_IE(hyperedge e) =
  rho * L_info_track(e)
+ (1-rho) * L_ledger(e)
+ lambda_anchor * Anchor_drift(e)
+ lambda_noether * Noether_violation(e)
```

这使“相对坐标关系”可以在高层被测度关系替代：

```text
relative relation(a,b) := d_IE(a,b), not raw coordinate distance
```

但底层坐标链仍保留。

### 5.3 测地线注意力的安全表达

注意力路径不是“沿真实测地线走”，而是：

```text
attention_path_candidate = argmin_topk S_IE[Gamma]
```

并保留偏离权：

```text
anti_geodesic_probe
random_exploration_budget
novelty_escape_channel
```

避免注意力永远沿既有度规自我强化。

---

## 6. 相对运动 / 相对静止的变分读出

上层“运动 / 静止”不能直接写成语义标签，只能作为只读关系读出。

### 6.1 相对静止 proxy

```text
relative_rest_proxy(a,b) =
  d_IE(a,b) remains bounded over K windows
  and conjugate_momentum_IE small
  and Xin_var low
  and ledger_balance_residual stable
```

其中共轭动量代理：

```text
p_IE_m = partial L_IE / partial (z_{m+1} - z_m)
```

### 6.2 相对运动 proxy

```text
relative_motion_proxy(a,b) =
  d_IE(a,b) changes persistently
  or p_IE_m has directional persistence
  or Xin_var forms directional gradient
  and change is not explained by noise budget
```

禁止解释：

```text
relative_motion_proxy != true motion
relative_rest_proxy != true physical rest
```

它们只是上层标签语义的候选投影。

---

## 7. 与外部熵账本的关系

外部熵账本不再只是记录：

```text
D, N, A, W, F_ext
```

而是为变分泛函提供约束面：

```text
ledger balance residual B_m
entropy production D_m
noise budget N_m
anomaly mass A_m
Noether violation
```

但外部账本仍然：

```text
read-only
cannot write P/R/Xin
cannot promote truth
cannot define semantic labels
```

---

## 8. 建议新增 schema

### 8.1 `v361_run_manifest`

| 字段 | 说明 |
|---|---|
| run_id | v36.1 run id |
| base_version | v36 blueprint / v35H sidecar |
| variational_functional_enabled | 1 |
| external_ledger_read_only | 1 |
| source_facts_rewritten | 0 |
| action_can_modify_mainline | 0 |
| metric_is_proxy | 1 |
| scientific_run_allowed | 0 |

### 8.2 `v361_variational_state_vector`

记录每个窗口的变分状态向量。

| 字段 | 说明 |
|---|---|
| state_id | 状态ID |
| window_id | 窗口 |
| p_mass | P质量 |
| r_mass | R质量 |
| xin_mass | Xin质量 |
| anomaly_mass | 异常质量 |
| dissipation | 耗散 |
| noise_budget | 噪声预算 |
| entropy_gap | 熵闭合缺口 |
| masking_strength | 屏蔽强度 |
| attention_intensity | 注意力强度 |
| hyperedge_weight | 超边权重 |
| anchor_drift | 坐标锚漂移 |

### 8.3 `v361_ledger_balance_residual`

| 字段 | 说明 |
|---|---|
| residual_id | ID |
| window_id | 窗口 |
| delta_F_ext | F_ext变化 |
| W_ext | 外部源项 |
| N | 噪声预算 |
| D | 耗散 |
| A | 异常差额 |
| B_residual | 账本不闭合残差 |
| residual_class | noise / structured / novelty / drift |

### 8.4 `v361_lagrangian_term`

| 字段 | 说明 |
|---|---|
| term_id | 项ID |
| path_id | 路径ID |
| window_id | 窗口 |
| term_name | track / ledger / diss / xin / r / mask / anchor / noether |
| term_value | 项值 |
| coefficient | 权重 |
| coefficient_meta_proxy_id | 权重的meta-proxy登记 |

### 8.5 `v361_action_functional`

| 字段 | 说明 |
|---|---|
| action_id | 作用量ID |
| path_id | Gamma路径 |
| S_IE | 总作用量代理 |
| S_tilde | 增强拉格朗日作用量 |
| ledger_residual_sum | 账本残差累计 |
| anomaly_struct_sum | 结构性异常累计 |
| path_status | candidate / ranked / rejected / appealable |
| forbidden_interpretation | 固定说明 |

### 8.6 `v361_euler_lagrange_residual`

| 字段 | 说明 |
|---|---|
| el_id | ID |
| path_id | 路径 |
| window_id | 窗口 |
| EL_norm | stationarity residual |
| EL_P_component | P分量 |
| EL_R_component | R分量 |
| EL_Xin_component | Xin分量 |
| EL_ledger_component | 账本分量 |
| EL_anchor_component | 坐标锚分量 |
| Xin_var | 变分Xin |

### 8.7 `v361_information_energy_metric`

| 字段 | 说明 |
|---|---|
| metric_id | ID |
| from_ref | 起点 |
| to_ref | 终点 |
| path_id | 路径 |
| d_IE | 信息—能量测度距离 |
| mu_IE_mean | 平均测度密度 |
| anchor_drift | 坐标锚漂移 |
| metric_status | provisional / unstable / guarded |
| metric_is_proxy | 必须为1 |

### 8.8 `v361_relation_readout_proxy`

| 字段 | 说明 |
|---|---|
| readout_id | ID |
| pair_ref | a,b |
| readout_type | relative_motion_proxy / relative_rest_proxy / ambiguous |
| d_IE_trend | 测度趋势 |
| p_IE_trend | 共轭动量趋势 |
| Xin_var_trend | 变分Xin趋势 |
| can_write_semantic_label | 必须为0 |

### 8.9 `v361_variational_guardrail_audit`

| 字段 | 说明 |
|---|---|
| audit_id | ID |
| check_name | 检查项 |
| status | PASS / FAIL / WARN |
| details | 详情 |

---

## 9. Runtime sidecar

建议目录：

```text
runtime_store/v361/
  variational_paths_v361.jsonl
  lagrangian_terms_v361.jsonl
  euler_lagrange_residual_v361.jsonl
  information_energy_metric_v361.jsonl
  relation_readout_v361.jsonl
  variational_guard_events_v361.jsonl
  meta_proxy_coefficients_v361.json
```

高频计算放 sidecar，SQLite 仅存摘要、索引、manifest、验收结果。

---

## 10. Acceptance 标准

```text
1. 所有 Lagrangian coefficients 必须登记为 meta-proxy。
2. 外部账本只读，不能写 P/R/Xin。
3. S_IE / S_tilde 不得命名为 truth loss。
4. Xin_var 必须由 EL residual + ledger residual + constraint residual 得出。
5. d_IE 只能在 admissible hyperedge neighborhood 内计算。
6. anchor_drift 超限时必须触发 metric_drift_warning。
7. relation_readout_proxy 不能写 semantic label。
8. relative_motion/rest 只能作为只读 proxy。
9. scientific_run_allowed 必须为0。
10. 若 ledger residual 高但 SNR 高，不得直接优化抹平，必须进入 novelty / Xi 审查。
```

---

## 11. 风险与对策

| 风险 | 描述 | 对策 |
|---|---|---|
| 变分泛函真理化 | 把最小作用量路径当成真实路径 | forbidden interpretation + proxy registry |
| 残差清零诱惑 | 优化器抹平 novelty | SNR-first residual classification |
| 账本参数漂移 | meta-proxy 改变导致度规剧变 | metric_anchor_audit + coefficient registry |
| 自我指涉测地线 | 注意力永远沿自己定义的低作用量路径走 | anti-geodesic probe + exploration budget |
| 离散拓扑不可导 | 对 hyperedge 做伪连续变分 | continuous features autograd, discrete topology control experiments |
| 语义越权 | 把 relation_readout 写成标签 | can_write_semantic_label=0 |

---

## 12. 与 v36 的关系

v36 原先的：

```text
Delta Xin / curvature proxy / dissipative source metric
```

在 v36.1 中被重写为：

```text
variational Xin / action residual / information-energy functional metric
```

保留：

```text
稳态耗散源
信息—能量测度
相对关系读出
拓扑热浴
坐标锚审计
暗吸引子测试
```

修改：

```text
Delta Xin 不再是主对象
curvature proxy 降为二级派生特征
metric 由路径泛函定义，而不是由局部差分定义
```

---

## 13. 一句话总结

> **v36.1 把 Xin 从“局部差分残余”提升为“外部账本约束下的信息—能量路径变分不闭合”。它不证明真实物理作用量，只在可审计的 proxy 边界内，为 Morphosphere 提供一个更自然的能量—信息测度求解框架。**
