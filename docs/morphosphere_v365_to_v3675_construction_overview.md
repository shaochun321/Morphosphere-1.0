# Morphosphere v36.5 到 v36.7.5 施工总览

**文档目的**：把从 v36.5 full-lineage rebase 到 v36.7.5 consolidated release candidate 的施工过程做一次总合，重点说明：理念如何演变、数理代理如何落地、为什么这样落实、实际落实到哪些 DB / 表 / 运行层，以及项目改进前后的流程与结构变化。

**文档定位**：这是施工总览与设计审计，不是营销文案，也不是单纯部署说明。它试图把“哲学 - 数学 - 工程 - 数据 - 边界”统一讲清楚。

**当前最终状态**：v36.7.5 是一个非破坏性工程硬化 Release Candidate。它不是 Online Native Runtime，不是生命式在线运行，也不是旧 DB 的破坏性迁移。它是在 v25-v36.5 的历史数据和 v36.6 的过程窗口基础上，建立了一套更硬的锚定、索引、guard、语义隔离与回归基线。

---

## 0. 一句话总览

从 v36.5 到 v36.7.5，Morphosphere 的施工主线可以概括为：

```text
v36.5:
  完成全谱系合流与 semantic stripping / external readout。

v36.6:
  把已有全链路数据物化成 process_window，建立信息点、轨迹、T/O/P/R/Xin、ledger、attention、hyperedge、variational、readout 的可查询链。

Pass10-Pass18:
  用实现覆盖度、上层实证、压力测试、泛化、source-level rerun、native-shaped replay 证明项目不是空跑，同时识别 direct FK、语义残留、P-core collapse、RMI 碰撞等工程债。

Pass19-Pass21:
  建立 v37 readiness gate、native writer facts、RMI H2/H3 索引基准、ledger binding 修复。

v36.7.1-v36.7.5:
  不破坏旧主线，把 native anchor、safe stress guard、semantic quarantine、RMI default index、coordinate invariance CI 固化成默认工程硬化基线。
```

最终形成的系统不是“一个单一算法”，而是一个多层离散关系系统：

```text
source / information point
-> coordinate / dark-grid audit
-> trajectory window / process_window
-> T/O/P/R/Xin role split
-> counter-evidence / masking
-> external entropy ledger
-> attention
-> hyperedge incidence
-> variational action / Xin_var
-> Xin carrier / external readout
-> native anchor / RMI / guard / regression baseline
```

---

## 1. 最核心的哲学 - 数学理念

### 1.1 真实输入先于语义解释

项目的第一原则是：信息不是从语义标签开始，而是从可审计的 source / information point / coordinate / trajectory 开始。语义解释只允许出现在 external readout 中，不能反写主线。

这导致了 v36.5 的核心决策：

```text
主线保留：carrier, measure, ledger, evidence, process, ref, hash。
外部模块保留：definition, semantic readout, hypothesis, risk flag, reentry suggestion。
禁止：semantic label -> P/R/Xin truth, source fact rewrite, Xin direct-to-P/R。
```

**为什么这样做**：如果语义标签进入主线，系统会把解释当成事实。Morphosphere 试图描述“信息如何形成轨迹和残余”，而不是先假设“这是什么”。

**落实方式**：v36.5 建立 Xin carrier / external definition / external readout / backwrite blocker；v36.7.3 将语义文本迁移到 quarantine sidecar，并生成 semantic-free view manifest。

---

### 1.2 坐标隐去，但不能删除

v36.6 的 process_window 不是坐标盒子，它试图把主线工作单位变成：

```text
W_k = (I_k, T_k, S_k, Π_k, E_k, L_k)

I_k: information payload / measure contribution
T_k: time span / ordering
S_k: support domain / kernel / bandwidth
Π_k: process operator / recursion trace
E_k: external envelope ref
L_k: external ledger ref
```

但“坐标隐去”不是“坐标删除”。坐标仍然是 evidence trace、raw event audit、3D/4D backprojection 和 metric drift check 的底座。

**为什么这样做**：如果主线只用显式坐标组织关系，就会把欧氏邻近误当成信息关系；如果完全删除坐标，又会使上层关系悬空。v36.6-v36.7 的折中是：主线以 process_window 组织，底层以 dark-grid / native anchor 审计。

**落实方式**：v36.6 建立 process_window 与 hypernode_spacetime_backprojection；v36.7.1 建立 v367_native_anchor_fact、dark_grid_zone_index 与 native backprojection。

---

### 1.3 T/O/P/R/Xin 是信息角色分离，不是语义分类

T/O/P/R/Xin 的角色不是标签体系，而是信息过程中的状态分解：

| 符号 | 角色 | 实际分离对象 |
|---|---|---|
| T | Trace / Trajectory / Transport / Time | 可追踪过程片段、时间窗口、轨迹支撑 |
| O | Object candidate / support candidate | 支撑候选，不是语义对象 |
| P | Positive support / relative stasis | 稳定支撑、相对静止、低账本压力结构 |
| R | Refutation / counterstructure | 持续反证、P 的挑战链、可拼接反证带 |
| Xin / Xi | Unclosed residual | 无法被 P/R/O 闭合但不能删除的残余 |

**为什么这样做**：项目试图回答“信息如何在过程里分化成稳定、反证和残余”，而不是回答“这个对象叫什么”。

**落实方式**：v25-v26 有 information point / coordinate transform / trajectory window / P/R/Xi measures；v36.2 引入 action score / stationarity defect / Xin_var；v36.3 引入 R-band；v36.5 引入 Xin carrier。

---

### 1.4 外部熵账本是治理账本，不是物理自由能本体

外部熵账本的作用是裁判：记录外部输入、耗散、噪声、anomaly、Noether-style gap、ledger residual。它不是 source truth，也不是物理自由能的真实测量。

**为什么这样做**：如果没有外部账本，P/R/Xin 的分离容易变成内部自洽游戏；如果把账本当物理本体，又会过度宣称。项目采用 proxy ledger：足以治理，但不冒充物理定律。

**落实方式**：v34/v34.1 外部熵账本与 proxy/meta-proxy；v36 引入 μ_IE；v36.2 引入 S_IE_proxy；v36.7.2 将安全应力包络转成 guard 配置。

---

### 1.5 高阶关系不是原生超图数据库，而是稀疏 incidence sidecar

v35H 的 hyperedge 不是把 SQLite 换成超图数据库，而是用 hyperedge / incidence 表表达多主体共同参与：P、R、Xin、masking、attention、ledger、proxy 可以共同组成一次高阶事件。

**为什么这样做**：项目需要表达“一个事件中多个角色共同参与”，但不应过早引入原生超图数据库或高维张量灾难。

**落实方式**：v35H 生成 120 条 hyperedge、855 条 incidence rows，平均 arity 约 7.125。v36.6 将 hyperedge process_window 化，v36.7 通过 native anchor 与 RMI 增强索引与回投。

---

### 1.6 变分、RMI、guard 都是代理工程，不是本体

v36.2 的 S_IE_proxy、v36.7 的 RMI、v36.7.2 的 safe stress guard 都是工程代理：

| 对象 | 正确定位 | 禁止过度宣称 |
|---|---|---|
| S_IE_proxy | 路径级账本代价函数 | 不是真实作用量 |
| stationarity_defect | 离散扰动缺陷 | 不是解析 Euler-Lagrange 证明 |
| Xin_var | 变分/账本/约束/anomaly 不闭合 | 不是真实物理场 |
| RMI | 关系测度索引 | 不是认知本体，也不能废除坐标审计 |
| Safe Stress Guard | 运行保护配置 | 不是新的 P/R/Xin 理论 |

---

## 2. 可还原的数理代理公式

以下公式是从 DB 结构、字段关系和测试结果中可较硬推导出的工程代理。它们是项目实际计算关系，不应被解释为真实自然定律。

### 2.1 轨迹几何

```text
mean_speed = path_length / duration

direction_coherence = net_displacement / path_length
```

含义：T 层首先把点状信息变成轨迹窗口，并计算路径长度、净位移、速度、一致性、曲率和带宽。

---

### 2.2 Attention tension

```text
attention_tension =
  0.35 * p_mass
+ 0.25 * r_counter_mass
+ 0.25 * xi_residual_mass
+ 0.15 * anomaly_mass
- 1.00 * boredom_decay
```

含义：attention 不是行动，也不是语义判断。它是 P/R/Xin/anomaly 与 boredom 的资源分配代理。

---

### 2.3 信息 - 能量测度 μ_IE

```text
mu_IE = rho * L_info_track + (1 - rho) * L_ledger
rho = 0.55

mu_IE = 0.55 * L_info_track + 0.45 * L_ledger
```

含义：v36 的关系几何不是纯坐标距离，而是信息轨迹成本与外部账本成本的组合。

---

### 2.4 曲率代理 K_proxy

```text
K_proxy =
  0.23 * abs_delta_xin
+ 0.19 * r_counter_mass
+ 0.17 * masking_tension
+ 0.24 * entropy_closure_gap
+ 0.17 * anomaly_persistence
- 0.15 * confirmed_p_inertia
```

含义：所谓曲率不是 Ricci curvature，而是局部不稳定压力：Xin 变化、反证、屏蔽张力、熵闭合缺口、anomaly 持续性共同推高，P 惯性降低。

---

### 2.5 Delta-Xin fallback

```text
delta_xin_clean = delta_xin_observed - noise_budget
```

含义：Delta-Xin 是局部残余变化扣噪声预算后的 fallback diagnostic，不是主 Xin 定义。

---

### 2.6 S_IE_proxy 路径代价

```text
S_IE_proxy =
  metric_kinetic_proxy
+ dissipation_cost
+ noise_cost
+ anomaly_cost
+ r_counter_cost
+ xin_mass_cost
+ noether_violation_cost
- legal_source_credit
```

含义：v36.2 将路径从局部窗口读数提升为账本代价排序，不寻找“真理路径”，只比较工程代理成本。

---

### 2.7 Stationarity defect

```text
stationarity_defect =
  |2 * current_score - left_perturbation_score - right_perturbation_score| / 2
```

含义：这是离散左右扰动下的二阶差分缺陷代理，不是解析变分证明。

---

### 2.8 Xin_var

```text
xin_var_total =
  el_residual_proxy
+ ledger_balance_residual
+ constraint_violation
+ unresolved_anomaly_mass
```

含义：主 Xin 从局部差分升级成“变分/账本/约束/anomaly 不闭合”的合计代理。

---

### 2.9 v36.4 Coupler cost

```text
c_total =
  1.0 * c_r_continuity
+ 0.8 * c_p_anchor
+ 1.1 * c_xin_residual
+ 0.7 * c_metric_distortion
+ 1.0 * c_ledger_violation
+ 0.9 * c_pseudo_smoothing
```

含义：R-band / coupler 在成本约束下寻找伪连续拼接，而不是证明真实连续流形。

---

### 2.10 RMI hash 变体

```text
H1 = HASH(measure category / coarse metric)
H2 = HASH(measure + trajectory/window anchor)
H3 = HASH(measure + dark-grid + trajectory + information/process anchor)
```

实测：H1 在混合空间出现 false-neighbor groups；H2/H3 在当前混合空间 false-neighbor 为 0。因此 v36.7.4 固化 H2/H3 为默认索引，H1 只保留为风险对照。

---

## 3. 项目改进前后的主流程对照

### 3.1 改进前：v36.5 刚合流时

| 层 | 状态 | 问题 |
|---|---|---|
| Base evidence | v25-v34 存在大量底层 DB / runtime_store | 分散，未统一成当前主线索引 |
| v35/v35H/v36.x overlay | 各层 DB 可运行 | 上层与底层 direct linkage 不够硬 |
| v36.5 semantic stripping | Xin carrier/readout 可用 | 主线语义剥离成功，但不是全链路物化 |
| full-rebase DB | coverage / boundary / acceptance | 只是合流证明，不是全量数据仓库 |
| Stage2 / preneural | 概念存在，部分被绕过 | 容易误判为缺失或失败 |
| 运行状态 | validation 通过 | validation 不等于实在数据链 |

### 3.2 改进后：v36.7.5

| 层 | 当前状态 | 作用 |
|---|---|---|
| full-chain materialized | m365_full_chain_materialized.db | 把已有数据串成物化全链路 |
| process_window | m366_process_window_pass3.db | 统一 information/time/support/process/ledger/envelope |
| empirical upper-layer | m366_upper_layer_empirical.db | 分析 P/R/Xin、attention、hyperedge、variational 的实证结果 |
| stress/generalization | Pass15-Pass18 | 验证坐标不变性、P/R/Xin 响应、01/02 泛化、source-level rerun |
| native anchor | v36.7.1 | 新增 855 native anchor facts，旧 direct_fk=0 保持历史诚实 |
| safe stress guard | v36.7.2 | 27 格安全压力包络变成 guard config |
| semantic quarantine | v36.7.3 | 36 条风险文本迁移/隔离 sidecar，生成 semantic-free views |
| RMI default index | v36.7.4 | H2/H3 作为默认关系测度索引，H1 只作为风险对照 |
| release candidate | v36.7.5 | 汇总所有 gate，形成硬化 RC |

---

## 4. 从 v36.5 到 v36.7.5 的版本施工矩阵

| 阶段 | 理念问题 | 工程落实 | 数据结果 | 边界 |
|---|---|---|---|---|
| v36.5 full-rebase | 全谱系合流、语义剥离 | m365_full_rebase.db、m365.db | v25-v36.5 coverage present，31 Xin carrier/readout | full-rebase DB 不是全量仓库 |
| full-chain materialization | validation 不等于数据 | m365_full_chain_materialized.db | 4,575 information points，13,941 trajectory links，532 T/O/P/R/Xin traces | 上层到底层仍部分 inferred |
| v36.6 process_window | 主线工作单位需从对象转为过程窗口 | m366_process_window.db / pass3 | 1,633 process windows，22,128 members | process_window 多数由物化整合生成，非原生 runtime |
| Pass10 coverage audit | 理念是否全部实现不清 | implementation coverage audit | 56 concepts 分成熟度 | BLUEPRINT_ONLY 不能当实现 |
| Upper-layer empirical | 项目到底识别什么 | m366_upper_layer_empirical.db | P/R/Xin role distribution，attention verdicts，hyperedge arity | 当前数据偏稳定，不是强新异 |
| Pass12/13 replay | 压力投影和样本重放 | native-shaped skeleton / replay | stress rows 3,192，replay samples 70 | native-shaped，不是 native runtime |
| Pass15 stress | n=1 与不变性问题 | rigid translation、warp、counter injection、01/02 compare | rigid translation PASS，02 sequence present | 02 仍只部分上层覆盖 |
| Pass16 rerun/anchor | 从测度投影向 source rerun | source-level rerun harness、anchor hash | rigid stable，counter/Xin WARN | P-core collapse 暴露脆弱性 |
| Pass17 hardening | directness/text/压力校准 | backprojection hardening、semantic audit、CTC02 overlay | L2 candidates 855，semantic review 36，safe rows 588 | L3 raw native FK 仍 0 |
| Pass18 writer/envelope | 原生写入和压力包络 | 100 writer prototype、safe envelope、semantic sidecar | CTC02 replay 60 samples，guard 初步 | prototype，不是 raw FK |
| Pass19 readiness | v37 条款可落地性 | v37 readiness matrix、RMI collision audit | READY_NOW 1，READY_WITH_DOWNGRADE 4 | Online runtime blocked |
| Pass20 writer/RMI | writer 扩展和 RMI 基准 | 855 writer facts，H1/H2/H3 benchmark | FK pass 848/855，H1 collision 3 | 7 ledger gaps |
| Pass21 ledger/RMI scale | 修 ledger 缺口，扩大 RMI | ledger repair，mixed 5,765 objects | operational FK 855/855，H1 false-neighbor 64，H3 0 | 848/855 strict historical hit |
| v36.7.1 anchor | 原生锚定基线 | native anchor fact 855 | anchor validation 855/855 | 旧 direct_fk=0 不改写 |
| v36.7.2 guard | 安全压力运行配置 | 27 guard rules | regression 27/27 | 不是在线熔断器 |
| v36.7.3 quarantine | 语义隔离生产迁移 | sidecar + semantic-free view manifest | quarantine rows 36，semantic regression 3/3 | 旧 DB 不破坏性删除 |
| v36.7.4 RMI baseline | 默认查询索引 | H2/H3 index | 11,530 index rows，false-neighbor 0 | H1 audit-only |
| v36.7.5 RC | 汇总门禁 | release candidate DB | PASS 9，WARN 1 | 7 strict ledger boundary preserved |

---

## 5. 改进前后流程图

### 5.1 v36.5 初始合流后的流程

```text
Base DB / runtime_store
  -> version overlay checks
  -> v35 attention
  -> v35H hyperedge
  -> v36.x variational / R-band / coupler
  -> v36.5 carrier / readout
  -> full-rebase coverage / acceptance
```

问题：这条链可以证明谱系存在和 overlay 可运行，但不能直接回答每个上层对象如何回到底层信息点，也不能把信息状态变化统一成 process_window。

### 5.2 v36.6 物化整合后的流程

```text
information point
  -> 3D/4D backprojection
  -> trajectory window
  -> T/O/P/R/Xin profile
  -> counter-evidence / masking
  -> external ledger
  -> attention
  -> hyperedge incidence
  -> variational path / Xin_var
  -> Xin carrier / external readout
  -> process_window
```

问题：这条链可以查询和分析，但许多连接是 materialized / inferred，不是上游模块原生写出。

### 5.3 v36.7.5 硬化后的流程

```text
information point / trajectory / evidence
  -> process_window
  -> native anchor fact
  -> dark-grid zone / composite anchor hash
  -> operational ledger binding
  -> safe stress guard action
  -> semantic-free mainline view
  -> RMI H2/H3 index
  -> regression gates
```

改进：同样的主线对象现在有更硬的证据锚、可配置 guard、语义隔离、关系测度索引和回归门禁。

限制：仍不是 online native runtime，也不是旧 DB 的破坏性迁移。

---

## 6. 数据落实总表

| 数据对象 | 当前数量 / 状态 | 来源 / 阶段 | 说明 |
|---|---:|---|---|
| information points | 4,575 | v25 / materialized | 底层真实/外部运动数据点 |
| trajectory links | 13,941 | full-chain materialized | 信息点到轨迹窗口关系 |
| T/O/P/R/Xin windows | 532 | v25 / empirical | 每个窗口有 P/R/Xin profile |
| counter-evidence chains | 532 | materialized | 反证链与 P/R/Xin 关联 |
| masking records | 52 | materialized / v35 | 屏蔽层记录，较少，不是全覆盖 |
| external entropy ledger events | 4,489 | v34/v36 materialized | 外部治理账本事件 |
| attention audits | 120 | v35 | NEUTRAL 79、EFFECTIVE 26、NOVELTY 5 |
| hyperedges | 120 | v35H | 高阶事件 |
| incidence rows | 855 | v35H | 平均 arity 约 7.125 |
| variational paths | 120 | v36.2 | action score / Xin_var |
| R-band candidates | 90 | v36.3 | 伪连续反证带 |
| Xin carriers / readouts | 31 | v36.5 | external readout 只读 |
| process_windows | 1,633 | v36.6 pass3 | 统一过程窗口 |
| process_window members | 22,128 | v36.6 pass3 | 跨层成员绑定 |
| native anchor facts | 855 | v36.7.1 | 非破坏性原生锚定基线 |
| safe stress rules | 27 | v36.7.2 | guard config |
| semantic quarantine rows | 36 | v36.7.3 | 解释性文本隔离 |
| RMI index rows | 11,530 | v36.7.4 | H2/H3 默认索引 |

---

## 7. 主线能力层 vs 工程硬化层

这是最近施工中最需要重新分清的边界。

### 7.1 主线能力层

| 模块 | 是否改变信息状态 | 说明 |
|---|---|---|
| information point / backprojection | 是 | 将原始观察转成可审计信息点 |
| trajectory / T | 是 | 点状信息变成过程片段 |
| O candidate | 是 / 部分隐式 | 支撑候选；Stage2 可合法绕过 |
| P | 是 | 稳定支撑 |
| R | 是 | 反证压力 / 反证链 |
| Xin | 是 | 不可闭合残余 |
| masking | 是 | 调节 R/Xin 暴露和屏蔽 |
| external entropy ledger | 是 / 治理 | 影响账本成本和闭合判断 |
| attention | 是 / 资源分配 | 决定继续看哪里 |
| hyperedge | 是 / 关系绑定 | 多主体高阶事件 |
| variational / S_IE_proxy | 是 | 路径级账本评分 |
| Xin carrier / readout | 是 / 分边界 | 主线 carrier 与外部解释分离 |

### 7.2 工程硬化层

| 模块 | 是否改变信息状态 | 正确定位 |
|---|---|---|
| native anchor fact | 不直接改变 | 增强证据锚定和可回投性 |
| dark-grid zone | 不直接改变 | 坐标审计与 hash 防碰撞 |
| RMI H2/H3 | 不直接改变 | 查询索引，不是认知本体 |
| safe stress guard | 不直接改变正常信息 | 运行保护与压力包络 |
| semantic quarantine | 不改变主线信息 | 防止解释性文本污染主线 |
| coordinate invariance CI | 不改变主线信息 | 回归门禁 |
| quick/complete bundle | 不改变 | 交付与复核工具 |

结论：v36.7 最近的大量施工主要属于工程硬化层。它们让主线更可靠，但不应被说成新主线能力。

---

## 8. 为什么这些改进必须落实

### 8.1 为什么要做 full-chain materialization

问题：早期 full-rebase 只能证明版本谱系齐全，不能证明全量数据从 source 到 readout 可追踪。

落实：构建 m365_full_chain_materialized.db。

效果：从 4,575 个 information points 到 532 个 T/O/P/R/Xin traces，再到 ledger / attention / hyperedge / readout 有了统一数据索引。

---

### 8.2 为什么要做 process_window

问题：上层对象分散在各版本 DB 中，无法统一描述信息过程。

落实：m366_process_window_pass3.db，1,633 process_windows，22,128 members。

效果：主线工作单位从“对象/表”转成“过程窗口”。

---

### 8.3 为什么要做 upper-layer empirical analysis

问题：用户真正关心项目识别/分离了什么，而不是测试是否通过。

落实：m366_upper_layer_empirical.db。

结果：P_STABLE_SUPPORT 65、R_COUNTER_PRESSURE 92、XIN_RESIDUAL_PRESSURE 201、attention verdicts 可见、hyperedge arity > 7。

效果：把理念变成可分析的数据分布。

---

### 8.4 为什么要做 stress/generalization

问题：n=1 数据集表现不能证明物性。

落实：Pass15 刚性平移、非刚性扭曲、counter injection、01/02 对比。

结果：rigid translation role_changed=0；nonrigid warp 局部压力不全局崩；01/02 JSD 低，统计轮廓相似。

效果：开始验证 P/R/Xin 分离是否对输入结构变化有合理响应。

---

### 8.5 为什么要做 native anchor hardening

问题：v36.6 hypernode 回投 855 条 direct_fk_available=0，上层关系有悬空风险。

落实：v36.7.1 新增 native anchor fact 855 条，旧表不改写。

效果：新增 v36.7 原生锚定基线，同时保留历史诚实。

---

### 8.6 为什么要做 RMI

问题：关系查询不能只靠空间邻近，也不能只靠粗测度 hash。

落实：Pass20/21/36.7.4 比较 H1/H2/H3；H2/H3 固化为默认索引。

结果：H1 在混合空间 64 个 false-neighbor groups；H2/H3 为 0。

效果：RMI 成为查询加速层，但不替代坐标审计。

---

### 8.7 为什么要做 safe stress guard

问题：Pass16/17 中 counter / Xin 压力能触发 R/Xin，但高强度或 P_core 注入会导致 collapse。

落实：v36.7.2 将 27 格 safe stress envelope 配置成 guard rules。

效果：系统知道哪些压力组合允许、审计、降尺度或阻断。

---

### 8.8 为什么要做 semantic quarantine

问题：主线相邻 DB 中可能存在解释性文本字段，虽然未必参与计算，但有语义污染风险。

落实：v36.7.3 迁移 36 rows 到 sidecar，生成 22 个 semantic-free view manifests。

效果：外部解释可以保留，但主线计算视图保持无语义。

---

## 9. 当前项目到底是什么

到 v36.7.5，Morphosphere 更准确地说是：

> 一个面向信息时空轨迹的离散关系构建与治理系统。它把原始信息点转成轨迹窗口，再分离为 P 稳定支撑、R 反证结构、Xin 不闭合残余，并通过外部熵账本、attention、hyperedge、variational path 与 external readout 构成可审计的多层信息过程系统。v36.7 则在不改写旧主线的前提下，为这条链加上 native anchor、RMI、guard、semantic quarantine 和 regression baseline。

它不是：

```text
- 完整在线生命 runtime
- 真实 PDE / 连续场求解器
- 原生超图数据库
- 语义分类器
- 已证明的物理理论
```

它是：

```text
- 信息轨迹分解系统
- P/R/Xin 状态分离系统
- 外部账本治理系统
- 高阶关系 incidence 系统
- 数据 lineage / observability 原型
- 非破坏性工程硬化基线
```

---

## 10. 改进前后的结构表

### 10.1 存储结构前后对比

| 维度 | 改进前 | 改进后 |
|---|---|---|
| 主要 DB 作用 | 版本/overlay/validation | materialized chain + process_window + anchor + index + guard |
| runtime payload | 分散 runtime_store | 保留，同时通过 materialized index 可查询 |
| 上层到底层引用 | 多为 inferred/proxy | v36.7 native anchor overlay 855/855 |
| 语义文本 | 可能混在 report/debug/core-adjacent 字段 | quarantine sidecar + semantic-free view |
| 索引 | SQLite table scan / source_ref | RMI H2/H3 default index |
| 压力响应 | projection / report | safe stress guard config |
| 交付 | 多个 pass 包 | v36.7.5 consolidated RC |

### 10.2 运行流程前后对比

| 运行阶段 | 改进前 | 改进后 |
|---|---|---|
| 数据输入 | source / CTC sequence | source + sequence split + coordinate invariance CI |
| 轨迹生成 | v25 trajectory windows | 统一进入 materialized chain |
| T/O/P/R/Xin | 有测度，但解释分散 | empirical role analysis + stress/generalization |
| 上层关系 | attention/hyperedge/variational 分散 | process_window 串联 |
| 回投 | proxy / inferred | native anchor overlay + dark-grid zone |
| 查询 | DB 表查询 | RMI H2/H3 mixed index |
| 压力测试 | 较少 | rigid/warp/counter/Xin/masking/semantic attack + guard |
| 发布状态 | full-rebase candidate | hardened release candidate |

### 10.3 模块边界前后对比

| 模块 | 过去容易误解 | 现在定位 |
|---|---|---|
| Stage2 | 被绕过 = 缺失 | 可合法绕过，类神经主体由 T/O/P/R/Xin + storage + ledger + external modules 承担 |
| RMI | 可能被说成认知本体 | 只作为关系测度索引 |
| semantic readout | 可能污染主线 | external readout only, semantic_write_allowed=0 |
| native anchor | 可能被误解为旧 DB direct FK | 新 v36.7 overlay fact，不改写 legacy |
| safe guard | 可能被说成新理论 | 运行保护配置 |
| release package | 可能被说成项目本体 | 只是交付与复核工具 |

---

## 11. 当前已知 WARN / 债务

| 债务 | 当前状态 | 处理方式 |
|---|---|---|
| 7 条 strict external entropy event hit 缺口 | operational ledger refs 855/855，但 strict historical hits 848/855 | 保留 WARN，不伪造历史 event |
| online native runtime | 未实现 | 未来 v37.0 prototype，小样本起步 |
| 100ms coordinate audit | 未实现 | 当前只有 coordinate invariance CI |
| async complex recursion | 未实现 | 暂不做，避免事务不一致 |
| CTC02 完整 native upper rerun | 部分 projection/replay | 未来逐步扩展 |
| external Xin taxonomy | 最小实现 | 未来外部模块完善 |
| P-core collapse under high stress | 已识别 | safe stress guard BLOCK/DOWNSCALE |

---

## 12. 下一阶段建议

虽然 v36.7.5 已经是硬化 Release Candidate，但不应马上宣称 v37 Online Native Runtime。下一步应回到 v36.8 Mainline Functional Integration，聚焦主线功能：

```text
1. 主线状态变化审计：信息点如何变成 T/O/P/R/Xin，再进入上层。
2. 行为准则落实：所有新增模块必须说明是否改变信息状态。
3. 主线能力优先于外围硬化：少做包和 gate，多做状态转移与识别/分离证据。
4. 外部模块保持只读：readout 不反写。
5. native anchor / RMI / guard 只作为支撑层使用。
```

如果要进入 v37，应先做小样本：

```text
v37.0 Native Runtime Prototype:
  50-100 条 source event
  -> information point
  -> process_window
  -> native anchor
  -> ledger binding
  -> guard action
  -> RMI lookup
  -> readout
```

不要一开始就做全量在线 runtime。

---

## 13. 最终结论

从 v36.5 到 v36.7.5，项目经历了三次性质变化：

1. **从谱系合流到全量物化**：v36.5 证明版本链齐全；v36.6 证明数据链可以串联。
2. **从物化整合到压力/泛化实证**：Pass12-Pass18 证明 P/R/Xin 与上层机制不是空概念，能在压力和跨序列中表现出可解释响应。
3. **从实证探索到工程硬化基线**：v36.7.1-v36.7.5 把 anchor、guard、quarantine、RMI、CI 固化为非破坏性基线。

但项目的主线仍然不是“部署包”或“索引系统”。主线始终是：

```text
information spacetime trajectory
-> T/O/P/R/Xin role separation
-> counter/masking/ledger governance
-> attention/hyperedge/variational relation building
-> Xin carrier / external readout
```

v36.7 做的是让这条主线更硬、更可审计、更可部署，而不是替代它。下一阶段应围绕主线功能整合继续，而不是继续无限小步硬化。
