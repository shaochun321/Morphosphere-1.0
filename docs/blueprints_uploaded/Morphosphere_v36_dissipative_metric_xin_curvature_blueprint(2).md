
# Morphosphere v36 蓝图：稳态耗散源、差分 Xin 与信息—能量测度曲率门

**版本定位**：`v36_dissipative_metric_and_xin_curvature_gate`  
**交付性质**：详尽蓝图，不是工程实现。  
**基线依赖**：v34 Proxy × External Entropy Control Plane、v34.1 Meta-Proxy Runtime Guard、v35 Attentional Path Integral Governance、v35H Hyperedge Incidence Sidecar。  
**新增固定条件**：从本蓝图开始，所有后续蓝图、实施报告、路线方案都必须包含一节：**“原哲学—数学构想如何降级、最小化并修正为工程对象”**。任何高阶数学/哲学概念都不得直接落入工程本体，必须给出降级版本、最小可运行代理、禁止解释和升级条件。

---

## 0. 摘要

v36 的目标不是宣称 Morphosphere 已经拥有真实连续流形、真实里奇流或真实物理度规，而是把用户提出的核心构想——

```text
稳定 T/O/P/R/Xin 递归节点
  -> 稳态耗散源
  -> 局部差分 Xin
  -> 信息—能量测度场
  -> 高层相对关系表达
  -> 只读语义投影：相对运动 / 相对静止
```

降级为一套**离散、稀疏、可审计、可回滚、受外部熵账本约束的工程 proxy 层**。

v36 的核心命题是：

> 坐标链保留外部可验证性；信息—能量测度提供内部关系几何。

也就是说，底层仍保留：

```text
raw coordinate
physical coordinate
origin-relative coordinate
coordinate_transform_trace
```

但在更高层的新原点关系中，系统可以额外引入：

```text
information_energy_metric_proxy
```

它用于表达两个结构在同一耗散时空中的关系强度、路径代价、局部曲率、相对变化趋势，而不是替代真实物理坐标。

---

## 1. 背景：为什么 v36 必须出现

v25-v35H 已经形成了相当完整的链路：

```text
v25 Evidence Reconstruction
v26 Shadow Cell-Sphere
v27 Reversible Measure Field
v28 Shadow-Evidence Divergence Gate
v28.1 Robust Divergence Hardening
v29 Intervention Policy Sandbox
v30 Hierarchical P Renormalization
v31 Active Inference Sandbox Loop
v31.1 Stabilization
v32 Generalized Source Adapter + Scale Contract
v33 Bottom Prediction Adapter
v34 Proxy × External Entropy Control Plane
v34.1 Meta-Proxy Runtime Guard
v35 Attentional Path Integral Governance
v35H Hyperedge Incidence Sidecar
```

这些版本解决了：证据链、shadow 审判、proxy 问责、外部熵账本、注意力治理、路径积分审计和逻辑超图索引。

但系统仍然缺少一个关键层：

```text
稳定结构之间的高层关系，不应永远依赖几何坐标差。
```

早期坐标关系回答的是：

```text
A 与 B 在坐标系中相距多远？
```

而 v36 要回答：

```text
A 与 B 在同一信息—能量耗散时空中，彼此发生关系需要付出多少账本代价？
它们的关系是持续变化、边界扰动、局部曲率异常，还是相对稳态？
```

这使系统从“外部观察者坐标”进一步走向“内部耗散关系”。

---

## 2. 固定新增条件：哲学—数学降级契约

### 2.1 为什么必须有降级契约

Morphosphere 现在已经频繁使用下列概念：

```text
外部熵
自由能
路径积分
马尔可夫毯
超图
信息—能量测度
局部曲率
里奇流
庞加莱式拓扑归约
相对运动 / 相对静止
```

这些概念有强烈的哲学和数学吸引力，但如果直接落入工程，会造成四类危险：

1. **概念实在化**：把 proxy 当作本体。
2. **数学越权**：把启发式指标冒充严格定理。
3. **工程不可算**：把连续微分、最优传输、全局曲率直接塞入离散稀疏系统。
4. **语义漂移**：把只读语义投影误当成系统内部真理。

因此从 v36 开始，所有蓝图必须包含：

```text
原哲学—数学构想
  -> 为什么不能直接实现
  -> 降级成什么工程对象
  -> 最小可运行版本是什么
  -> 修正/最小化策略是什么
  -> 禁止解释是什么
  -> 未来升级条件是什么
```

### 2.2 本蓝图的降级总表

| 原哲学—数学构想 | 直接实现风险 | v36 降级对象 | 最小化/修正版本 | 禁止解释 |
|---|---|---|---|---|
| 稳态耗散源 | 把迭代次数误认为热力学定态 | `v36_dissipative_source_registry` | K 窗口内 D/F_ext 方差低、SNR 高、证据锚未漂移 | 稳态源 ≠ 真实物理热源 |
| 微分 Xin 场 | 连续微分不可观测，易对噪声建几何 | `v36_delta_xin_field` | `ΔXin = Xin(t+1)-Xin(t)`，离散窗口差分 | ΔXin ≠ 连续场导数 |
| 信息—能量度规 | 把 ledger-unit 变成本体度规 | `v36_information_energy_metric_edge` | `μ_IE = ρ L_info + (1-ρ)L_ledger` | μ_IE ≠ 真实物理度规 |
| 测地线注意力 | 自我强化、错过新异性 | v35 attention path + v36 metric hints | top-k 候选 + off-geodesic exploration | 最短测度路径 ≠ 最正确路径 |
| 里奇流 | 连续 PDE、曲率计算爆炸 | `v36_curvature_proxy` | 由 ΔXin/R/Masking/entropy_gap 构成曲率 proxy | curvature_proxy ≠ Ricci curvature |
| 局部庞加莱 | 拓扑概念硬套离散事件 | topology fingerprint / local equivalence audit | 局部指纹去重和冗余归约 | topology_equivalent ≠ physical_identity |
| 势陷闭合 | 形成暗吸引子、屏蔽反证 | `v36_singularity_candidate` + shock test | 高曲率+高 SNR+持续异常才进入候选 | closed basin ≠ truth |
| 拓扑手术 | 删除超边造成账本失衡 | `v36_topological_heat_bath` | 剪枝耗散转入热浴，不直接消失 | GC ≠ 能量消失 |
| 相对运动/静止语义 | 高层标签越权 | `v36_relative_relation_readout` | 只读投影：d_IE 是否持续变化 | relation_readout ≠ semantic truth |

---

## 3. v36 的核心哲学边界

v36 的哲学立场可以压缩成四条：

### 3.1 坐标不消失

v36 不废除坐标链。坐标链仍然是外部可验证性、回放、反投、数据校验的硬支架。

```text
坐标链负责：在哪里。
信息—能量测度负责：在同一耗散时空中如何彼此存在。
```

### 3.2 能量不是焦耳

外部熵账本中的能量仍然是：

```text
ledger energy
effective energy
free-energy-like quantity
```

不是项目内部对象真实携带的焦耳意义物理能量。

### 3.3 Xin 不再只是垃圾桶

Xin / Xi 不再只是“不能归类的残余”。v36 把它分成两层：

```text
Xi surface:
  unresolved residual storage

Delta Xin field:
  residual change induced by stable dissipative source across windows
```

这意味着 Xin 具备动力学意义，但仍是 proxy。

### 3.4 语义只读

“相对运动 / 相对静止”只能作为只读投影，不得反写 P/R/Xi，也不得直接产生 semantic label。

---

## 4. 数学对象与工程降级

### 4.1 外部总平衡仍是根公式

v36 继续继承外部熵账本的平衡式：

```text
F_ext(m+1) - F_ext(m) = W_ext(m) + N(m) - D(m) - A(m)
```

其中：

```text
F_ext: 外部自由能账
W_ext: 合法外部源项 / 抽取项
N: 噪声预算
D: 耗散
A: 异常差额
```

v36 的关键修正是：

```text
对稳定递归节点而言，D 不一定是失败。
健康、持续、有界的 D 可以是稳态耗散源存在的证据。
```

### 4.2 稳态耗散源定义

原哲学—数学构想：

```text
一个稳定 P/R/Xin 递归节点，像非平衡定态耗散结构一样，持续耗散并维持局部有序。
```

直接实现风险：

```text
把“迭代次数多”误认为“定态”；把“稳定标签”误认为热力学稳态。
```

工程降级：

```text
v36_dissipative_source_registry
```

最小可运行定义：

```text
source_is_steady(s) =
  Var_K(D_ext_s) < ε_D
  and Var_K(F_ext_s) < ε_F
  and SNR_struct_s > θ_snr
  and anchor_drift_s < θ_anchor
  and source_facts_rewritten = 0
```

说明：

```text
K: 观察窗口数
D_ext_s: 外部账本归属到结构 s 的耗散
F_ext_s: 结构 s 的外部自由能账
SNR_struct_s: 结构性信噪比
anchor_drift_s: 与 raw/physical coordinate anchor 的偏移
```

禁止解释：

```text
steady_dissipative_source ≠ physical heat source
steady_dissipative_source ≠ biological stable organ
steady_dissipative_source ≠ confirmed truth
```

### 4.3 差分 Xin

原哲学—数学构想：

```text
稳态耗散源引发局部变量微分，产生微分 Xin 存在。
```

直接实现风险：

```text
当前系统没有连续可微流形，强行定义 ∂Xin/∂x 会把离散噪声几何化。
```

工程降级：

```text
v36_delta_xin_field
```

最小可运行定义：

```text
ΔXin_s(m) = Xin_s(m+1) - Xin_s(m)
```

平滑修正：

```text
ΔXin_smooth_s(m) = EMA_λ(ΔXin_s(m))
```

噪声校正：

```text
ΔXin_clean_s(m) = ΔXin_smooth_s(m) - E[N_xin_s(m)]
```

禁止解释：

```text
ΔXin_clean ≠ true differential field
ΔXin_clean ≠ biological signal
ΔXin_clean ≠ emergence by itself
```

### 4.4 信息—能量测度

原哲学—数学构想：

```text
能量流动作为与信息时空轨等效的信息—能量测度，替代新原点中信息矩阵间的坐标关系。
```

直接实现风险：

```text
把 ledger-unit 当作真实度规；把审计量变成本体；产生循环论证。
```

工程降级：

```text
v36_information_energy_metric_edge
```

最小可运行定义：

```text
μ_IE(a,b,m) = ρ · L_info_track(a,b,m) + (1-ρ) · L_ledger(a,b,m)
```

其中：

```text
L_info_track:
  信息时空轨成本，可来自 v35 attention path / v35H hyperedge incidence。

L_ledger:
  外部熵账本诱导的耗散、噪声、异常、Noether violation 成本。
```

建议展开：

```text
L_ledger(a,b,m) =
  η_D · D_path(a,b,m)
+ η_N · N_path(a,b,m)
+ η_A · A_path(a,b,m)
+ η_G · Noether_gap(a,b,m)
```

所有参数：

```text
ρ, η_D, η_N, η_A, η_G
```

必须登记到 v34.1 meta-proxy registry。

禁止解释：

```text
μ_IE ≠ physical distance
μ_IE ≠ biological energy
μ_IE ≠ truth metric
```

### 4.5 测度距离

原哲学—数学构想：

```text
相对坐标关系在信息时空轨约束下，与信息—能量测度等效。
```

工程降级：

```text
d_IE(a,b) = shortest_path_sum μ_IE over confirmed hyperedge neighborhood
```

重要限制：

```text
只在 confirmed hyperedge / attention path / Markov-neighbor 区域计算。
不做全局全对全距离。
不做全局最优传输。
```

最小算法：

```text
1. 从 v35H 读取 confirmed / appealable hyperedges。
2. 将 μ_IE 作为边权重。
3. 对局部邻域运行 Dijkstra / A*。
4. 得到 d_IE。
5. 写入 v36_metric_path_index。
```

禁止解释：

```text
d_IE ≠ actual spatial distance
d_IE ≠ causal proof
d_IE shortest path ≠ optimal biological route
```

### 4.6 局部曲率代理

原哲学—数学构想：

```text
在信息—能量测度场上形成局部曲率，类似里奇流 / 局部庞加莱思想，可用于压缩冗余、识别奇点。
```

直接实现风险：

```text
连续里奇流需要光滑流形、PDE、连续度规，当前系统是离散超边与账本 proxy。
```

工程降级：

```text
v36_curvature_proxy
```

最小公式：

```text
K_proxy(S,m) =
  a1 · |ΔXin_clean(S,m)|
+ a2 · R_counter_mass(S,m)
+ a3 · Masking_tension(S,m)
+ a4 · Entropy_closure_gap(S,m)
+ a5 · Anomaly_persistence(S,m)
- a6 · Confirmed_P_inertia(S,m)
```

解释：

```text
高 K_proxy:
  局部结构处于强张力 / 强反证 / 强残余变化 / 强异常持续状态。

低 K_proxy:
  局部结构稳定或低影响。
```

禁止解释：

```text
K_proxy ≠ Ricci curvature
K_proxy ≠ geometric truth
K_proxy ≠ biological membrane curvature
```

### 4.7 奇点候选

原哲学—数学构想：

```text
当信息—能量测度场中的局部曲率极高时，可能出现认知奇点、势陷闭合或涌现事件。
```

工程降级：

```text
v36_singularity_candidate
```

最小判定：

```text
singularity_candidate(S,m) =
  K_proxy(S,m) > θ_K
  and SNR_struct(S,m) > θ_snr
  and Anomaly_persistence(S,m) > θ_persist
  and Noise_budget_explained(S,m) = false
```

分型：

```text
STRUCTURED_NOVELTY
DARK_ATTRACTOR_RISK
NOISE_SPIKE
METRIC_DRIFT
TOPOLOGICAL_BOTTLENECK
```

禁止解释：

```text
singularity_candidate ≠ true emergence
singularity_candidate ≠ physical singularity
singularity_candidate ≠ semantic discovery
```

---

## 5. “相对运动 / 相对静止”的只读语义投影

### 5.1 原哲学—数学构想

```text
信息—能量测度的值暗合上层标签语义：相对运动与相对静止。
```

### 5.2 直接实现风险

```text
把测度变化直接命名为“运动”；把测度稳定直接命名为“静止”；导致语义越权。
```

### 5.3 工程降级

```text
v36_relative_relation_readout
```

### 5.4 最小定义

相对运动 proxy：

```text
relative_motion_proxy(a,b) =
  Var_K(d_IE(a,b)) > θ_d
  and mean_K(|ΔXin_path(a,b)|) > θ_xin
  and directionality_asymmetry(a,b) > θ_dir
```

相对静止 proxy：

```text
relative_rest_proxy(a,b) =
  Var_K(d_IE(a,b)) < ε_d
  and mean_K(|ΔXin_path(a,b)|) < ε_xin
  and Var_K(D_ext_path(a,b)) < ε_D
```

### 5.5 禁止解释

```text
relative_motion_proxy ≠ object is physically moving
relative_rest_proxy ≠ object is physically static
```

允许解释：

```text
系统检测到两个结构在信息—能量测度场中的关系持续变化 / 保持有界。
```

---

## 6. v36 schema 草案

### 6.1 `v36_run_manifest`

| 字段 | 说明 |
|---|---|
| run_id | v36 run id |
| base_version | v35H / v34.1 |
| source_facts_rewritten | 必须为 0 |
| metric_proxy_enabled | 是否启用信息—能量测度 proxy |
| continuous_geometry_claimed | 必须为 0 |
| ricci_flow_claimed | 必须为 0 |
| semantic_label_write_enabled | 必须为 0 |
| created_at | 时间 |

### 6.2 `v36_downgrade_contract_register`

用于固定记录哲学—数学降级。

| 字段 | 说明 |
|---|---|
| contract_id | 降级契约 ID |
| original_concept | 原哲学—数学概念 |
| direct_implementation_risk | 直接实现风险 |
| downgraded_engineering_object | 降级后的工程对象 |
| minimal_operational_form | 最小可运行形式 |
| correction_strategy | 最小化/修正策略 |
| forbidden_interpretation | 禁止解释 |
| future_upgrade_condition | 升级条件 |

### 6.3 `v36_dissipative_source_registry`

| 字段 | 说明 |
|---|---|
| source_id | 稳态耗散源 ID |
| source_ref | 对应 P/R/Xin/macro/hyperedge |
| source_type | confirmed_p / macro_candidate / stable_r / xin_structure |
| window_span | K 窗口范围 |
| D_variance | 耗散方差 |
| F_ext_variance | 外部自由能方差 |
| SNR_struct | 结构信噪比 |
| anchor_drift | 坐标锚漂移 |
| steady_status | candidate / accepted / rejected |
| proxy_provenance_id | proxy 来源 |

### 6.4 `v36_delta_xin_field`

| 字段 | 说明 |
|---|---|
| delta_xin_id | 差分 Xin ID |
| source_id | 关联耗散源 |
| window_id | 当前窗口 |
| xin_prev | 上一窗口 Xin mass |
| xin_curr | 当前窗口 Xin mass |
| delta_xin_raw | 原始差分 |
| delta_xin_smooth | EMA 平滑 |
| noise_budget | 噪声预算 |
| delta_xin_clean | 噪声校正后差分 |
| interpretation | stable / rising / falling / noisy / structured |

### 6.5 `v36_information_energy_metric_edge`

| 字段 | 说明 |
|---|---|
| metric_edge_id | 测度边 ID |
| node_a_ref | 结构 A |
| node_b_ref | 结构 B |
| hyperedge_ref | v35H 超边引用 |
| L_info_track | 信息时空轨成本 |
| L_ledger | 账本成本 |
| rho | 混合权重 |
| mu_IE | 信息—能量测度 |
| parameter_registry_refs | meta-proxy 参数引用 |
| metric_status | active / provisional / rejected |

### 6.6 `v36_metric_path_index`

| 字段 | 说明 |
|---|---|
| path_id | 测度路径 ID |
| start_ref | 起点 |
| end_ref | 终点 |
| path_hyperedges | 局部超边序列 |
| d_IE | 累积测度距离 |
| path_algorithm | dijkstra / astar / beam |
| locality_scope | confirmed_hyperedge_neighborhood / attention_path |
| global_search_enabled | 必须为 0 |

### 6.7 `v36_metric_anchor_audit`

| 字段 | 说明 |
|---|---|
| audit_id | 审计 ID |
| metric_edge_id | 测度边 |
| raw_coordinate_delta | 原坐标差变化 |
| physical_coordinate_delta | 物理坐标差变化 |
| mu_IE_delta | 测度变化 |
| drift_class | normal / metric_drift / coordinate_drift / ledger_parameter_drift |
| guardrail_action | none / warn / block / recalibrate |

### 6.8 `v36_curvature_proxy`

| 字段 | 说明 |
|---|---|
| curvature_id | 曲率 proxy ID |
| region_ref | 局部区域 |
| delta_xin_component | ΔXin 分量 |
| r_counter_component | R 反测度分量 |
| masking_component | 屏蔽张力分量 |
| entropy_gap_component | 熵闭合缺口 |
| anomaly_component | 异常持续项 |
| p_inertia_component | P 惯性项 |
| K_proxy | 局部曲率 proxy |
| risk_class | low / medium / high / singularity_candidate |

### 6.9 `v36_singularity_candidate`

| 字段 | 说明 |
|---|---|
| singularity_id | 奇点候选 ID |
| region_ref | 区域 |
| curvature_id | 曲率 proxy 引用 |
| SNR_struct | 信噪比 |
| anomaly_persistence | 异常持续 |
| noise_explained | 是否可由噪声解释 |
| singularity_type | STRUCTURED_NOVELTY / DARK_ATTRACTOR_RISK / NOISE_SPIKE / METRIC_DRIFT / TOPOLOGICAL_BOTTLENECK |
| recommended_action | deep_audit / shock_test / heat_bath / metric_recalibration / ignore |

### 6.10 `v36_topological_heat_bath`

| 字段 | 说明 |
|---|---|
| heat_bath_id | 热浴 ID |
| removed_ref | 被剪枝 / GC 的对象 |
| removal_reason | high_dissipation / rejected_future / topology_gc / noether_violation |
| transferred_dissipation | 转入热浴的耗散 |
| transferred_anomaly_mass | 转入热浴的异常质量 |
| ledger_balance_ref | 外部账本平衡引用 |
| noether_status | pass / warn / fail |

### 6.11 `v36_dark_attractor_shock_test`

| 字段 | 说明 |
|---|---|
| shock_id | 冲击测试 ID |
| target_source_id | 目标稳态源 |
| shock_type | counterevidence / noise / masking_release / metric_perturbation |
| shock_strength | 冲击强度 |
| response_delta_xin | 反应 ΔXin |
| recovery_windows | 恢复窗口数 |
| verdict | elastic_stable / dark_attractor / fragile / inconclusive |

### 6.12 `v36_relative_relation_readout`

| 字段 | 说明 |
|---|---|
| readout_id | 只读投影 ID |
| node_a_ref | A |
| node_b_ref | B |
| d_IE_variance | 测度距离方差 |
| delta_xin_mean | 平均 ΔXin |
| D_ext_variance | 耗散方差 |
| relation_proxy | relative_motion_proxy / relative_rest_proxy / unstable_relation_proxy |
| semantic_write_allowed | 必须为 0 |

### 6.13 `v36_acceptance_report`

| 字段 | 说明 |
|---|---|
| check_id | 检查项 |
| status | PASS / WARN / FAIL |
| details | 说明 |
| blocking | 是否阻断 |

---

## 7. Runtime sidecar 设计

```text
runtime_store/v36/
  delta_xin_field_v36.jsonl
  information_energy_metric_edges_v36.coo.jsonl
  metric_path_index_v36.jsonl
  curvature_proxy_v36.jsonl
  singularity_candidates_v36.jsonl
  topological_heat_bath_v36.jsonl
  shock_test_events_v36.jsonl
  downgrade_contract_v36.json
  metric_guardrail_events_v36.jsonl
```

策略：

```text
SQLite:
  存 manifest、索引、摘要、acceptance、审计结果。

runtime_store:
  存高频 ΔXin、局部测度边、路径索引、冲击测试事件。

不存密集全局矩阵。
不存全局连续场。
不做全局最优传输。
```

---

## 8. 核心算法流程

### 8.1 识别稳态耗散源

```text
for each candidate stable structure s:
  collect D_ext, F_ext, SNR, anchor_drift over K windows
  if Var(D_ext)<ε_D and Var(F_ext)<ε_F and SNR>θ and anchor_drift<θ_anchor:
      register s as dissipative_source_candidate
  else:
      reject or keep provisional
```

### 8.2 计算差分 Xin

```text
for each dissipative source s:
  for each window m:
    delta_raw = Xin_s(m+1) - Xin_s(m)
    delta_smooth = EMA(delta_raw)
    delta_clean = delta_smooth - expected_noise_budget
    write v36_delta_xin_field
```

### 8.3 构建信息—能量测度边

```text
for each local pair / hyperedge-neighbor (a,b):
  L_info = attention / hyperedge / information track cost
  L_ledger = D_path + N_path + A_path + Noether_gap
  mu_IE = rho * L_info + (1-rho) * L_ledger
  write v36_information_energy_metric_edge
```

### 8.4 局部路径距离

```text
for each local query (a,b):
  build local graph from confirmed hyperedge neighborhood
  use mu_IE as edge weight
  run Dijkstra / A*
  write d_IE to v36_metric_path_index
```

### 8.5 锚点漂移审计

```text
if |delta(mu_IE)| is high and raw/physical coordinate delta is low:
  classify metric_drift or ledger_parameter_drift
  trigger v34.1 runtime guard / recalibration
```

### 8.6 曲率 proxy 与奇点检测

```text
for each local region S:
  K_proxy = weighted sum of ΔXin, R, masking, entropy gap, anomaly, P inertia
  if K_proxy high and SNR high and anomaly persistent and noise not explanatory:
      create singularity_candidate
```

### 8.7 拓扑热浴

```text
for each pruned hyperedge / rejected future / topology GC object:
  do not delete ledger mass
  transfer dissipation/anomaly to topological_heat_bath
  verify Noether balance
```

### 8.8 暗吸引子冲击测试

```text
for each too-stable dissipative source:
  inject sandbox shock
  observe ΔXin response and recovery
  if no response to meaningful counterevidence:
      classify dark_attractor_risk
  if elastic recovery:
      classify elastic_stable
```

---

## 9. Guardrails

### 9.1 物理与几何禁止解释

```text
information_energy_metric_proxy ≠ physical spacetime metric
curvature_proxy ≠ Ricci curvature
singularity_candidate ≠ physical singularity
relative_motion_proxy ≠ object truly moving
relative_rest_proxy ≠ object truly static
```

### 9.2 写权限边界

```text
v36 不得改写：
  source facts
  v25 information points
  coordinate_transform_trace
  external entropy ledger raw events
  P/R/Xi 主链事实
```

### 9.3 账本边界

```text
外部熵账本可以约束 v36 metric proxy。
但 v36 metric proxy 不得反写外部熵正本。
```

### 9.4 语义边界

```text
relative relation readout 只能输出只读 proxy。
不能生成 semantic label。
不能反向强化 P/R。
```

### 9.5 探索边界

为了防止测地线注意力自我强化，必须保留：

```text
off-geodesic exploration budget
random perturbation budget
appeal_registry re-entry
```

---

## 10. Acceptance 标准

### 10.1 降级契约验收

```text
每个高阶概念必须在 v36_downgrade_contract_register 中登记。
没有降级契约的数学概念不得进入 active pipeline。
```

### 10.2 稳态源验收

```text
所有 dissipative_source 必须有外部熵账本证据。
不得仅凭迭代次数或命名稳定性进入。
```

### 10.3 Xin 验收

```text
ΔXin 必须由窗口差分计算。
必须记录噪声预算。
不得称为连续微分场。
```

### 10.4 测度验收

```text
μ_IE 参数必须登记为 meta-proxy。
metric edge 必须绑定 hyperedge 或 attention path。
不得进行全局全对全测度计算。
```

### 10.5 锚点验收

```text
metric drift 必须与 raw/physical coordinate anchor 对比。
坐标锚不许删除。
```

### 10.6 曲率验收

```text
curvature_proxy 必须明确 formula_version。
不得称为 Ricci curvature。
```

### 10.7 奇点验收

```text
singularity_candidate 必须同时满足 K_proxy、SNR、persistence、noise_not_explanatory。
不得直接升级为 emergence。
```

### 10.8 热浴验收

```text
任何 topology GC / pruning 都必须把耗散和异常质量转入 topological_heat_bath。
不得让账本质量消失。
```

### 10.9 语义验收

```text
relative_relation_readout.semantic_write_allowed = 0
```

---

## 11. 与 v35 / v35H / v37 的关系

### 11.1 对 v35 的作用

v36 为 v35 注意力路径提供新测度：

```text
attention tension
  + path integral
  + information_energy_metric
  -> better attention proposal ranking
```

但 v36 不能让注意力直接越权。

### 11.2 对 v35H 的作用

v36 使用 v35H 的 hyperedge incidence sidecar 构建局部测度邻域。

```text
v35H provides:
  hyperedge nodes
  incidence weights
  ledger-weighted hyperedge status

v36 adds:
  local μ_IE
  d_IE path index
  curvature proxy
  heat bath accounting
```

### 11.3 对 v37 的前置意义

v37 若进入 sparse tensor / runtime graph backend，需要 v36 先证明：

```text
局部信息—能量测度是否有预测力？
ΔXin 是否比随机更能预测未来耗散变化？
K_proxy 是否能提前识别真实高价值异常？
```

若这些都不成立，v37 不应扩大计算后端。

---

## 12. 风险清单

| 风险 | 描述 | v36 对策 |
|---|---|---|
| metric 本体化 | 把 μ_IE 当作真实时空度规 | 明确 provisional_metric_proxy |
| 噪声几何化 | 把随机 Xi 变化当曲率 | SNR + noise budget + persistence 联合判定 |
| 度规漂移 | meta-proxy 改变导致全局关系漂移 | metric_anchor_audit + raw coordinate anchor |
| 暗吸引子 | 屏蔽层过厚导致死闭合 | shock_test |
| 热量消失 | 剪枝超边直接 delete | topological_heat_bath |
| 语义越权 | 运动/静止变标签 | readout only, semantic_write_allowed=0 |
| 全局计算爆炸 | 全局最优传输/全对全测距 | 只算局部 confirmed hyperedge neighborhood |
| 坐标链被替代 | 可验证性丢失 | 坐标链不可删除，不可反写 |

---

## 13. 未来升级条件

v36 只有在满足以下条件后，才允许考虑更强的几何 / 拓扑 / runtime 后端：

```text
1. ΔXin 能稳定预测未来 D_ext / A_path 的变化，优于随机基线。
2. μ_IE 距离与外部熵账本审计结果有稳定相关性。
3. metric_anchor_audit 显示账本参数漂移不会破坏全局关系。
4. curvature_proxy 能提前识别高价值 anomaly / emergence candidate。
5. heat_bath 保持 Noether-style balance 不失衡。
6. shock_test 能区分 elastic stable 与 dark attractor。
```

如果以上不成立，则 v36 必须停留在 proxy metric 层，不得升级为几何 runtime。

---

## 14. 固定模板：后续所有蓝图必须包含

从本蓝图开始，每个版本都必须包含以下表格：

| 项 | 内容 |
|---|---|
| 原哲学—数学构想 | 原始高阶概念是什么 |
| 直接实现风险 | 为什么不能直接工程化 |
| 降级工程对象 | 实际落成什么表 / runtime / sidecar |
| 最小可运行形式 | 最小算法 / 最小数据结构 |
| 修正策略 | 如何避免越权、过拟合、不可算 |
| 禁止解释 | 不允许怎样解释 |
| 升级条件 | 什么证据足够后可提升成熟度 |

这不是格式要求，而是项目治理要求。

---

## 15. 一句话总结

**v36 不把信息—能量测度宣布为真实时空，而是把它降级为由外部熵账本、差分 Xin、局部超边和坐标锚共同约束的 provisional metric proxy。**

它允许 Morphosphere 第一次用耗散关系替代高层新原点中的简单坐标关系，但仍保留底层坐标链、外部账本边界、proxy 身份和语义只读原则。

```text
坐标告诉系统对象在哪里。
信息—能量测度告诉系统对象在同一个耗散时空中如何彼此存在。
```
