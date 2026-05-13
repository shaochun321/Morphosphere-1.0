# Morphosphere 下一阶段计划（v34-v40）

**版本定位**：阶段性战略蓝图，面向 v33 之后的下一阶段。  
**建议阶段名**：`multisource_causal_active_runtime_phase`  
**日期**：2026-05-03  
**状态**：计划方案，不是 scientific_run，不是 final biology，不授权真实行动。

---

## 0. 摘要

v25-v33 已经把 Morphosphere 从“真实数据可进入系统”推进到“统一来源、可审判预测、沙盒行动闭环、底层预测回归”的阶段。下一阶段不应继续盲目堆表，也不应直接宣称主动生命系统完成。下一阶段的核心任务是：

1. **把 runtime 从 SQLite 压力中剥离出来**：SQLite 保持 ledger/index/audit，所有高频状态进入 tensor / graph / chunk sidecar。
2. **验证多源泛化能力**：内部底层、外部真实物理数据、shadow prediction、simulation source 都必须进入统一 source-event 与 scale-contract。
3. **把 v33 bottom prediction 真正放进 v28/v31 的审判回路**：底层不再只是 legacy，也不直接夺权，而是成为可惩罚、可确认、可进入 Xi 的 prediction source。
4. **把 confirmed P 从“稳定结构”推进到“因果宏观节点”**：只有经过干预沙盒、有效信息 proxy、跨尺度稳定性测试的 P 结构，才允许成为 higher-order substrate。
5. **建立稳健主动系统前的安全边界**：action 继续 sandbox-only；source facts 不改写；Xi 不能直接转 P/R；自由能继续标注为 proxy。

建议路线：

```text
v34 Runtime Tensor/Graph Backend
v35 Multisource Physical Evidence Adapter
v36 Bottom Prediction vs Evidence Trial
v37 Policy Learning / Expected Free-Energy Proxy
v38 Causal Macro-Node and Effective Information Audit
v39 Multiscale Active Runtime Prototype
v40 Release Candidate / Scientific Boundary Audit
```

---

## 1. 当前基线：v25-v33 已经完成什么

| 版本 | 核心作用 | 当前状态 |
|---|---|---|
| v25 | Evidence Reconstruction Store：信息点、坐标链、轨迹窗口、P/R/Xi 测度、evidence bundle | 已实现 |
| v26 | Shadow Cell-Sphere：真实数据生成旁路 shadow bottom | 已实现 |
| v27 | Reversible Measure Field：可逆查询、measure cell、反投索引 | 已实现 |
| v28 | Shadow-Evidence Divergence：预测与证据碰撞 | 已实现 |
| v28.1 | Robust Divergence Hardening：precision、control、runtime/ledger audit | 已实现 |
| v29 | Intervention Policy Sandbox：行动提案与沙盒重放 | 已实现 |
| v30 | Hierarchical P Renormalization：confirmed P 到宏观候选节点 | 已实现 |
| v31 | Embodied Active Inference Loop：sandbox-only 策略闭环 | 已实现 |
| v31.1 | Release Candidate Stabilization：v25-v31 总审计 | 已实现 |
| v32 | Generalized Source Adapter + Scale Contract | 已实现 |
| v33 | Bottom Prediction Adapter：早期底层作为 prediction source 回归 | 已实现 |

**关键边界仍应保持**：

```text
source_facts_rewritten = 0
hot_swap_allowed = 0
real_action_authorized = 0
legacy_direct_active_allowed = 0
xi_direct_to_pr_allowed = 0
```

当前阶段的风险不是“没有结构”，而是结构已经足够复杂，必须开始向 runtime、泛化、多源、因果审计和鲁棒性验证转移。

---

## 2. 下一阶段的核心问题

### 2.1 运行载体问题

SQLite 已经被正确定位为 ledger/index/audit；但如果未来继续把高频 tick、edge state、trace field、action replay、policy cycle 都逐行写入 SQLite，会重新进入 IO 绞杀。下一阶段必须把高频状态迁移到 runtime sidecar。

推荐原则：

```text
SQLite:
  - manifest
  - index
  - source digest
  - summary snapshot
  - acceptance
  - anomaly / alert

Runtime sidecar:
  - dense tensor
  - sparse graph
  - event field
  - trace field
  - action rollout
  - policy posterior samples
  - multi-scale support fields
```

### 2.2 泛化问题

v32 已经建立 general source adapter 和 scale contract，但还需要真实验证：

```text
internal bottom event
external physical evidence
shadow prediction
simulation source
sensor stream
```

能否都进入同一条白盒链路：

```text
source_event -> information_point / event_field -> coordinate_transform -> trace_window -> O/P/R/Xi -> divergence/sandbox
```

### 2.3 因果与行动问题

v29/v31 已有 sandbox-only action loop，但它仍是 diagnostic proxy。下一阶段不能直接让 action 改写真实底层，而应让 action 只做三类事情：

```text
1. 请求更高采样密度
2. 请求 targeted replay / perturbation
3. 在 shadow / bottom prediction source 中测试策略
```

然后把结果交给 divergence gate 审判。

### 2.4 层级问题

v30 已经产生 macro-node candidate，但还不能把所有 confirmed P 直接打包成宏观细胞。宏观节点必须经过 causal / effective-information proxy 审计。

---

## 3. 成熟理论与项目参考

### 3.1 Predictive Coding：上下行预测与残差

Rao & Ballard 的 predictive coding 模型将高层到低层的反馈解释为预测，把低层到高层的前馈解释为预测误差。这与 Morphosphere 的 Shadow-Evidence divergence 十分接近：Shadow 提供预测，Evidence 提供误差，P/R/Xi 负责测度分解与治理。

在 Morphosphere 中对应为：

```text
Top-down prediction  -> shadow_edge / bottom_prediction_edge / policy_prior
Bottom-up residual   -> evidence_edge - shadow_edge
Residual routing     -> confirmed P / R / Xi / emergence
```

### 3.2 Active Inference：感知与行动的双重误差最小化

Active inference 的关键不是“系统能行动”，而是行动必须服务于预测误差或 expected free-energy 的降低。Morphosphere 可以吸收这个思想，但必须保持诚实：当前只能实现 `expected_free_energy_proxy`，不能宣称实现严格变分自由能。

对应为：

```text
perception-like path:
  update shadow / policy belief to explain evidence

action-like path:
  propose sandbox intervention to sample, perturb, or replay a region
```

### 3.3 Optimal Control as Inference：策略选择可写成分布匹配问题

控制可被表述为推断问题：寻找策略，使轨迹分布接近偏好轨迹分布，同时付出控制成本。Morphosphere 可以把 action sandbox 写成 KL / cost proxy，而不是直接把上层命令灌入底层。

### 3.4 World Models：在 shadow/sandbox 中训练策略，再回到 evidence 审判

World Models 的思想提醒 Morphosphere：可以在内部模型或 shadow world 中先测试策略，但策略绝不能因为在模型里成功就直接改写现实。Morphosphere 应保持：

```text
shadow rollout success -> policy_candidate only
policy_candidate -> evidence/divergence validation -> promotion gate
```

### 3.5 Causal Emergence / Effective Information：宏观节点必须证明因果效应

confirmed P 不能仅凭稳定性成为宏观节点。它必须在干预下表现出对上层结构的可测影响。可以采用 effective information proxy：比较 macro intervention 与 micro intervention 对未来状态分布或 O/P/R/Xi 测度的约束力。

### 3.6 OpenWorm / Brian2 等工程参考

OpenWorm 的经验说明：底层生物结构、力学、神经连接、环境和行为必须通过工具栈协同，而不是一个数据库解决一切。Brian2 的经验说明：神经/前神经动力学更适合由可表达微分方程与可切换硬件后端的 runtime 承担，而不是把每个 tick 都写入审计数据库。

---

## 4. 数理核心：下一阶段建议的统一形式

### 4.1 Source Event

统一源事件定义：

```text
e_i = (source_id, source_kind, t_i, x_i, y_i, z_i, c_i, v_i, u_i, provenance_i)
```

其中：

- `source_kind`：external evidence / internal bottom / shadow prediction / sandbox action / simulation
- `(t_i, x_i, y_i, z_i)`：时空位置
- `c_i`：通道，如 motion、force、phase、edge、entropy、voltage
- `v_i`：观测或预测值
- `u_i`：不确定度或噪声估计
- `provenance_i`：来源、recipe、hash、adapter、scale contract

### 4.2 坐标与尺度契约

每个源必须给出尺度映射：

```text
phi_s: X_raw^s -> X_canonical
```

并记录：

```text
scale_contract_s = {
  time_unit,
  spatial_unit,
  dimensionality,
  sampling_rate,
  uncertainty_model,
  window_policy,
  aggregation_policy
}
```

### 4.3 Evidence-Shadow/Prediction Divergence

对每个窗口 `W_k` 和支撑域 `Ω_k`：

```text
D_k = Σ_j w_j * d_j(E_k, S_k)
```

其中可分解为：

```text
D_k = w_edge d_edge
    + w_traj d_traj
    + w_measure d_measure
    + w_time d_time
    + w_space d_space
    + w_topology d_topology
    + w_entropy d_entropy
    + w_xi d_xi
```

### 4.4 Precision-weighted Divergence

引入精度：

```text
γ_k = sigmoid(a * SNR_k + b * persistence_k + c * reliability_k - d * uncertainty_k)
```

加权散度：

```text
D_k^γ = γ_k * D_k
```

低精度噪声不应击穿上层结构；高精度 persistent surprise 应进入 Xi/emergence 或触发 targeted replay。

### 4.5 P/R/Xi 分解

仍保持：

```text
Y_k = P_k + R_k + Xi_k + ε_num + ε_ext
```

其中：

```text
P_k = confirmed stable occupancy measure
R_k = counter-occupancy / competing explanation / calibration drift
Xi_k = unresolved residual surface with reentry via O only
```

### 4.6 Action Sandbox / Expected Free-Energy Proxy

策略 `π` 不直接作用于 reality，而是作用于 sandbox：

```text
π: state_context -> intervention_proposal
```

定义 proxy：

```text
G_proxy(π) = E_q[D^γ_after(π)]
           + λ_cost C(π)
           - λ_info I_proxy(π)
           + λ_risk R_risk(π)
```

其中：

- `D^γ_after(π)`：行动后加权散度
- `C(π)`：行动成本，如采样、扰动、计算资源
- `I_proxy(π)`：信息增益 proxy，如 Xi 下降、uncertainty 下降、confirmed P 上升
- `R_risk(π)`：越权风险，尤其是可能污染 source facts 的风险

选择策略：

```text
π* = argmin_π G_proxy(π)
```

但 `π*` 仍然只进入 proposal / sandbox，不授权真实行动。

### 4.7 Effective Information Proxy for Macro Node

宏观节点候选 `M` 来自 confirmed P 集群。它必须通过干预测试：

```text
EI_proxy(M) = I(Z_{t+1}; do(M_t = m)) - I(Z_{t+1}; do(micro_t))_baseline
```

工程近似可以用：

```text
EI_proxy(M) = H(Z_{t+1}) - H(Z_{t+1} | do(M_t)) - penalty_degeneracy
```

只有满足：

```text
EI_proxy(M) > threshold
stability(M) > threshold
source_contamination_risk = 0
```

的宏观节点，才允许成为 higher-order substrate candidate。

---

## 5. 下一阶段版本路线

### v34 Runtime Tensor/Graph Backend

**目标**：把高频 runtime 从 SQLite 剥离出来。  
**新增对象**：

```text
v34_runtime_tensor_manifest
v34_sparse_graph_manifest
v34_async_ledger_commit
v34_runtime_checkpoint
v34_runtime_ledger_boundary_report
```

**交付**：

- `runtime_store/v34/event_field.*`
- `runtime_store/v34/trace_field.*`
- `runtime_store/v34/edge_state_graph.*`
- `outputs/m34.db` 只保存 ledger/index

**验收**：

```text
high_frequency_rows_in_sqlite = 0 for active runtime
SQLite quick_check = ok
runtime checkpoint hash verified
async ledger summaries complete
```

### v35 Multisource Physical Evidence Adapter

**目标**：接入至少两类非 CTC 来源的模拟或真实物理数据，并验证统一 source-event 管线。  
**候选来源**：

```text
3D CTC / volumetric microscopy
traction-force microscopy-like dataset
calcium / voltage imaging-like stream
synthetic foam-grid mechanical field
```

**新增对象**：

```text
v35_external_source_adapter
v35_physical_unit_mapping
v35_cross_source_calibration
v35_multisource_evidence_bundle
```

**验收**：

```text
at least 2 source kinds mapped to general_source_event
coordinate_system_contract exists for each source
scale_contract exists for each source
trajectory/field window generated without source-specific hacks
```

### v36 Bottom Prediction vs Evidence Trial

**目标**：让 v33 bottom predictions 与 v25/v35 evidence 正式相撞。  
**新增对象**：

```text
v36_bottom_evidence_alignment
v36_bottom_prediction_divergence
v36_bottom_confirmed_structure
v36_bottom_false_prediction_penalty
v36_bottom_missing_prediction_xi
```

**验收**：

```text
bottom prediction confirmed > 0
bottom overreach rows > 0 or justified zero
bottom surprise rows > 0 or justified zero
legacy modules still prediction_only
```

### v37 Policy Learning / Expected Free-Energy Proxy

**目标**：把 v29/v31 的 action sandbox 从静态策略推进到可学习 policy prior。  
**新增对象**：

```text
v37_policy_prior
v37_policy_posterior
v37_expected_free_energy_proxy
v37_policy_counterfactual_rollout
v37_policy_safety_audit
```

**验收**：

```text
policy posterior updated by sandbox outcomes
no real_action_authorized
expected_free_energy_proxy decreases for accepted policies in sandbox
risk penalty blocks unsafe policies
```

### v38 Causal Macro-Node and Effective Information Audit

**目标**：对 v30 macro node 做因果审计，防止宏观节点只是形状聚类。  
**新增对象**：

```text
v38_macro_intervention_test
v38_effective_information_proxy
v38_macro_node_promotion_gate
v38_macro_node_rejection_report
```

**验收**：

```text
EI_proxy computed for each macro candidate
macro promotion requires intervention effect
promotion does not rewrite source facts
macro nodes remain audit/runtime substrate, not source truth
```

### v39 Multiscale Active Runtime Prototype

**目标**：把 source-event、bottom prediction、policy sandbox、macro node 串成多尺度 runtime loop。  
**新增对象**：

```text
v39_multiscale_runtime_cycle
v39_cross_scale_attention_request
v39_macro_to_micro_prediction
v39_micro_to_macro_residual
v39_runtime_stability_report
```

**验收**：

```text
micro->macro residual flow present
macro->micro attention request present
runtime loop checkpointed in sidecar
ledger summaries remain bounded
```

### v40 Release Candidate / Scientific Boundary Audit

**目标**：阶段封版，不新增能力，进行科学边界、工程边界、下载边界和 reproducibility 审计。  
**新增对象**：

```text
v40_phase_inventory
v40_boundary_audit
v40_reproducibility_manifest
v40_known_proxy_register
v40_pending_science_register
```

**验收**：

```text
all active versions check pass
all proxy claims labeled
no final biology claim
no scientific_run claim unless external criteria met
```

---

## 6. 数据结构草案

### 6.1 `v34_runtime_checkpoint`

| 字段 | 说明 |
|---|---|
| checkpoint_id | runtime checkpoint id |
| version | v34 |
| runtime_path | sidecar path |
| tensor_count | number of tensors |
| graph_count | number of sparse graphs |
| time_range | covered time range |
| sha256 | sidecar digest |
| ledger_summary_ref | SQLite summary |

### 6.2 `v35_multisource_evidence_bundle`

| 字段 | 说明 |
|---|---|
| bundle_id | bundle id |
| source_kind | source type |
| adapter_id | source adapter |
| scale_contract_ref | scale contract |
| coordinate_contract_ref | coordinate transform contract |
| event_refs | source events |
| field_refs | runtime field chunks |
| uncertainty_model | uncertainty type |

### 6.3 `v36_bottom_prediction_divergence`

| 字段 | 说明 |
|---|---|
| divergence_id | id |
| bottom_prediction_ref | bottom prediction |
| evidence_ref | evidence edge/window |
| temporal_delta | time mismatch |
| spatial_delta | spatial mismatch |
| measure_delta | measure mismatch |
| entropy_delta | external entropy mismatch |
| status | confirmed / overreach / surprise / shifted |

### 6.4 `v37_expected_free_energy_proxy`

| 字段 | 说明 |
|---|---|
| policy_id | policy |
| cycle_id | sandbox cycle |
| divergence_before | weighted divergence before |
| divergence_after | weighted divergence after |
| information_gain_proxy | information gain |
| action_cost | cost |
| risk_penalty | risk |
| efe_proxy | final score |

### 6.5 `v38_effective_information_proxy`

| 字段 | 说明 |
|---|---|
| macro_candidate_id | macro node candidate |
| intervention_ref | intervention test |
| entropy_before | H before |
| entropy_after_conditioned | H after conditioned on intervention |
| degeneracy_penalty | penalty |
| ei_proxy | effective information proxy |
| promotion_status | promoted / rejected / needs_more_data |

---

## 7. 验收矩阵

| 能力 | 必须验收 |
|---|---|
| Runtime/Ledger 分离 | 高频 runtime 不逐 tick 写 SQLite |
| 多源泛化 | 至少两类新 source_kind 通过统一 adapter |
| 底层回归 | legacy/bottom 只能 prediction-only，结果被 divergence 审判 |
| Action | action 只能 sandbox；不能改写 source facts |
| Precision | 低精度噪声权重下降，高持续 surprise 权重上升 |
| Macro | 宏观节点必须通过 EI proxy / intervention effect |
| Xi | Xi 只能 via O candidate re-entry |
| Reproducibility | manifest、sha256、query CLI、acceptance 都存在 |

---

## 8. 风险与反模式

### 8.1 反模式：为了行动而行动

不要让 v37/v39 变成“系统会命令底层”。行动必须始终是 sandbox proposal，除非未来有外部硬件/实验 gate。

### 8.2 反模式：把 free-energy proxy 当成真正自由能

继续使用 proxy 标签。严格自由能需要完整生成模型、后验分布、偏好分布和变分推断，目前 Morphosphere 不应宣称已完成。

### 8.3 反模式：宏观节点成为形状聚类

宏观节点必须基于 intervention effect / effective information proxy，而不是单纯 based on P overlap。

### 8.4 反模式：SQLite 复吸高频 runtime

如果 v34 之后继续把 tick-level 状态全写 SQLite，就会重犯 IO 错误。

### 8.5 反模式：多源 adapter 做成多条孤岛管线

所有来源必须进入同一 `general_source_event` / `scale_contract` / `coordinate_contract`，不能为每个数据源写一套特殊主线。

---

## 9. 近期优先级

建议顺序：

```text
第一优先级：v34 Runtime Tensor/Graph Backend
第二优先级：v36 Bottom Prediction vs Evidence Trial
第三优先级：v35 Multisource Physical Evidence Adapter
第四优先级：v37 Policy Learning / EFE Proxy
第五优先级：v38 Macro EI Audit
```

原因：若不先解决 runtime/ledger，后续多源和 action 会使 SQLite 压力扩大；若不尽快审判 bottom prediction，v33 回归仍停留在“接入”而非“证明”；若不做多源 adapter，泛化能力仍无法证明。

---

## 10. 下一步可直接施工的 v34 最小范围

v34 不需要大理论。最小可施工版本：

```text
1. 扫描 outputs/m33.db 中疑似高频表
2. 标记 runtime-only / ledger-only / hybrid
3. 生成 runtime_store/v34/checkpoints/*.jsonl 或 .npz
4. SQLite 只保存 checkpoint manifest 和 summary
5. 添加 check_v34.py 验证：runtime hash、ledger summary、quick_check、boundary audit
```

建议先不要引入 GPU 或复杂图数据库。先做：

```text
JSONL/NPZ + SQLite manifest
```

等结构稳定后，再选择 Zarr、Arrow/Parquet、PyTorch sparse、JAX array 或图数据库。

---

## 11. 最后判断

下一阶段不是简单做“更聪明”的系统，而是做“更可运行、更可泛化、更可审判”的系统。

核心句：

```text
Runtime 承担高频生命活动；SQLite 承担审计与记忆；
Bottom 负责提出预测；Evidence 负责提供反证；
Policy 负责提出沙盒行动；Divergence 负责审判；
Macro 只有在因果上有效时，才允许成为更高层。
```

这才是 v33 之后合理的下一阶段。

---

## 参考资料（用于理论映射，不等同于项目已实现声明）

1. Karl Friston, “The free-energy principle: a unified brain theory?”, Nature Reviews Neuroscience, 2010.
2. Thomas Parr & Karl Friston, “Generalised free energy and active inference”, Biological Cybernetics, 2019.
3. Rajesh P. N. Rao & Dana H. Ballard, “Predictive coding in the visual cortex”, Nature Neuroscience, 1999.
4. Hilbert J. Kappen, Vicenç Gómez, Manfred Opper, “Optimal control as a graphical model inference problem”, Machine Learning, 2012.
5. David Ha & Jürgen Schmidhuber, “World Models”, 2018.
6. Erik Hoel et al., work on effective information / causal emergence; use cautiously as proxy guidance, not as settled doctrine.
7. OpenWorm project: bottom-up organism simulation and neuromechanical modelling as cautionary reference.
8. Brian2: spiking neural-network simulation framework with equations, units and code-generation lessons.
