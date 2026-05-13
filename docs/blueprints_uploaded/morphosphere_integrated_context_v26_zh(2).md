
# Morphosphere 项目整合文档（截至 v2.6）

本文用于在当前对话框上下文即将达到极限前，尽可能完整地还原本轮讨论、判断、修正和工程实施路线。它不是宣传稿，也不是“科学完成声明”。它是一个面向继续开发、复盘、迁移和防止上下文丢失的技术—哲学—工程整合文档。

## 0. 文档边界

本项目在对话中经历了多个阶段：从 v8.5.3 的诊断物理基线，到 state separation、dynamic recursion、P/R restoration、online sensorium、matrix-foam、device-neutral edge、external lab、runtime/ledger split、field runtime、真实 CTC 数据接入、证据重构、shadow cell-sphere reconstruction。许多版本曾因下载体积、环境卡顿、overlay/层包问题而出现交付形态不稳定。本文以当前可复核的逻辑链为准，并明确哪些已经实现、哪些只是 proxy、哪些仍未完成。

最重要的边界如下：

- 项目目前不是 final biology。
- 项目目前不是严格 scientific_run。
- 真实 CTC 数据已经接入，但它验证的是真实细胞运动轨迹入口，不是完整力学、基质、牵引力或膜电生理。
- SQLite 已被重新定位为 ledger/index，不应继续作为高频 runtime 心脏。
- P/R/Xi 是审计、测度与治理层，不应该成为未来类神经 runtime 的黑箱本体。
- 真实数据不能直接覆盖旧底层事实；只能投影、对照、生成 shadow bottom，或在严格 gate 后生成新 run。

## 1. 原始理念：信息被时空结构出来

用户的核心理念反复强调：信息结构不是凭空从符号或语义标签中产生的，也不是先有“信息结构”再反算时空。正确顺序应是：

```text
真实时空结构 / 物理运动
  -> 细胞球底层受力、位移、形变、轨迹、相位、连续性
  -> 原始无语义事件点
  -> 轨迹与支撑域
  -> O candidate
  -> P/R 分解
  -> masking / 反证链 / 外部熵账本
  -> Xi 残余存储面
  -> 未来类神经结构的审计反馈与注意力调度
```

项目的核心不是给图像、运动或对象贴标签，而是从真实时空变化中分离出不同运动状态和信息轨迹。用户希望底层细胞球像真实物理对象一样存在：细胞球内有细胞，细胞之间有泡沫网格、基质或组织样承载层，细胞受力后产生信号，信号进入前神经层，再形成 T/O/P/R/Xi 等跨层结构。

程序和现实不同。程序由表、文件、runtime sidecar、接口、适配器和审计账本构成。为了避免丢失原始理念，项目每次新增工程层时都必须回答：

- 这个字段或表是否有真实来源？
- 它是否能反投到时间、空间、细胞、轨迹、事件？
- 它是否只是 summary score？
- 它是否越权替代了真实物理或 P/R/Xi？
- 它是否能成为未来类神经结构的原料？

## 2. v8.5.3 的定位：诊断物理基线，不是完整物理生命

早期工程 v8.5.3 已经具备若干重要能力：

- `spacetime_cell`：底层时空细胞记录。
- `information_fiber`：信息纤维记录。
- `transport_current_edge`：transport 代价、接受/拒绝边。
- `relation_entropy_record`：关系熵诊断。
- `o_candidate_record`、`pr_confirmation_graph_record`、`xi_residue_record` 等诊断表。
- manifest、provenance、acceptance、forbidden use、scientific_run=false 等治理结构。

但它不是完整物理细胞球。它缺少真实细胞形状、真实 ECM/泡沫网格、真实膜电/钙信号、真实力学方程、真实多模态输入。它更接近一个“诚实标注自己是 diagnostic system 的审计账本和诊断链路”。

从这里开始，后续版本不是要简单堆更多表，而是要逐渐让项目从审计账本走向：真实数据入口、状态分离、递归动态、物理侧车、证据重构和 shadow bottom。

## 3. state_separation_v0.1：无语义状态分离层

v0.1 的目标是把底层时空/纤维事件转换成无语义 raw event，再形成 origin anchor、latent trajectory 和 Xin residual。核心链路是：

```text
spacetime_cell + information_fiber
  -> raw_event_stream
  -> origin_anchor
  -> latent_trajectory
  -> trajectory_event_binding
  -> xin_residue_state
  -> trajectory_reprojection_report
```

这一层重要之处在于：它不从语义对象开始，而是从连续性、相位、守恒性、回投误差等关系中尝试分离运动状态。它验证了真实项目应该先形成“轨迹材料”，而不是先声明“这是什么对象”。

局限：v0.1 仍是一次性离线诊断，不是动态神经系统。

## 4. dynamic_recursive_v0.2：递归动态层

v0.2 把一次性分解推进为跨 tick 的动态递归：

```text
raw_event_stream
  + separated cell_spatial_coordinate_snapshot
  + information_relative_coordinate_snapshot
  + system_clock_entry
    -> preneural_node_state / preneural_edge_state
    -> dynamic_origin_anchor_state
    -> dynamic_latent_trajectory_state
    -> topdown_feedback_signal
    -> xin_residue_dynamics
    -> recursive_memory_trace
```

此版本明确了两件事：

1. 产生信息的细胞空间坐标与信息相对坐标必须分开存储。  
2. `system_clock_entry` 是实际递归时间源；空的旧 `system_clock` 表不能被误当成 source-of-truth。

局限：当时 P/R 被 latent trajectory 和 Xin 阴影化，导致用户指出 P/R 似乎被 Xin 顶替。这是后续修复的重要原因。

## 5. pr_restoration_xi_boundary_v0.2.2：恢复 P/R 主线

用户指出：P/R 不应该被 Xin/Xi 顶替。原始链路应为：

```text
Transport -> O -> P/R -> masking -> Xi
```

修复后的正统边界：

- P = positive / predictive structural support，但更后续应升级为空间—时间占据测度。
- R = refutational counter-structure，不是 residual。
- Xi = unresolved residue carrier，不是 R，也不是垃圾桶。
- Xi 不能直接生成 P/R。Xi 若要回主线，只能经 O_candidate re-entry。

这一修复非常关键，因为它避免了 dynamic Xin 成为主处理器，也避免 R 被误写成 residual。

## 6. online_sensorium_v0.3：逐 tick 在线递归

v0.3 引入在线递归层：

```text
system_clock_entry[n]
  -> raw_event_stream at clock_n
  -> online_preneural_tick_state
  -> online_origin_anchor_tick
  -> online_latent_trajectory_tick
  -> online_o_candidate_tick
  -> online_p_support_tick
  -> online_r_counterstructure_tick
  -> online_xi_boundary_tick
  -> online_feedback_tick
```

它进一步把 replay 从“报告级 counterfactual”推进为复制事件 buffer 后重新跑诊断响应。它保留 P/R before Xi，禁止 Xi 直接生成 P/R，禁止 top-down feedback 改写 source facts。

## 7. matrix_foam_physical_driver_v0.4：底层基质/泡沫代理

v0.4 开始补用户最初想象中的“泡沫网格/基质/结缔/肌肉样承载层”。新增：

- `substrate_material_region_v04`
- `cell_matrix_contact_v04`
- `foam_edge_state_v04`
- `substrate_stress_tensor_v04`
- `mechanotransduction_event_v04`
- `physical_sample_stream_v04`

但这仍是 diagnostic physical proxy，不是最终 ECM 生物学，不是 FEM/PDE 求解器。它的价值是把“细胞球里有基质和泡沫承载层”从纯文本推进为可检查的结构。

## 8. device_neutral_preneural_edge_v0.5：设备中立前神经边

v0.5 引入类忆阻/OECT/易失突触边的设备中立接口：

- `ideal_memristive_edge`
- `noisy_rram_like_edge`
- `volatile_memristive_edge`
- `oect_ionic_edge`

它模拟 conductance、memory、hysteresis、retention、noise、plasticity，但不宣称真实硬件接入。它只是为未来类神经边提供协议。

## 9. active_inference_lab_v0.6 与 v0.7-v1.8：外部实验室、冻结配置与拒绝 hot-swap

v0.6 建立外部只读系统辨识/主动推理 proxy 实验室，生成候选权重，但不自动应用。

v0.7 建立 candidate adoption gate 和真实数据校准入口。

v0.8 关闭 shell0 为“结构性边界历史遗留问题，并保留 physical watchlist”。

v0.9 建立真实外部物理数据入口和人工审查包。

v1.0 将 runtime 与 SQLite ledger 分离。

v1.1 建立外部物理模拟器 sidecar。

v1.2 建立 Zarr-style chunked field runtime。

v1.3 让 online sensorium 能读取 field chunks。

v1.4-v1.6 处理队列、backpressure、多时钟同步、漂移记忆。

v1.7-v1.8 建立 frozen profile promotion gate 和 sandbox replay。

贯穿这些版本的原则是：不做 hot-swap。外部实验室可以提建议，但不能直接替换主线参数。候选 profile 必须经 replay、真实数据、P/R-Xi 边界、source digest、人工批准后，作为新的 frozen profile 从头重跑。

## 10. v1.9-v2.4：真实 CTC 数据接入

用户询问如何接入真实数据：是替换底层还是镶嵌到底层？回答是：默认不替换底层，而是把真实外部观测投影/镶嵌到细胞球/前神经相应层上。只有未来通过严格 gate，才允许生成新 run 或 shadow bottom。

选择真实数据源时，我们选了 Cell Tracking Challenge（CTC），而不是 EEG 或牵引力显微。原因：CTC 最贴近“底层细胞球提供运动状态信息”的主线。

v2.0 选择 `Fluo-N2DH-GOWT1` 作为优先真实数据源。

v2.1 建立下载、校验、解包、centroid 提取工具。

v2.2 建立 declared trial 编排器。

v2.3 审计用户上传的真实执行结果 DB。

v2.4 用户上传原始 `Fluo-N2DH-GOWT1.zip` 后，完成真正源 ZIP 路径：

- source ZIP entries = 803
- sequence_count = 2
- centroid rows = 4575
- track_count = 86
- source ZIP SHA256 = `1a7bd9a7d1d10c4122c7782427b437246fb69cc3322a975485c04e206f64fc2c`
- real declaration gate = `PASS_REAL_EXTERNAL_DECLARED`

这证明真实 CTC 数据已经进入项目。但它验证的是真实 2D 细胞/细胞核运动轨迹，而不是真实 3D 细胞球、基质应力或 mechanotransduction。

## 11. 为什么先用 2D 数据

2D CTC 数据的作用是验证真实运动轨迹入口、轨迹提取、映射、P/R/Xi 响应、系统不崩溃和不画靶。它不是最终 3D 物理，也不证明底层细胞球完备。

项目底层仍然存在：

- `spacetime_cell`
- `information_fiber`
- `raw_event_stream`
- `cell_spatial_coordinate_snapshot`
- `information_relative_coordinate_snapshot`
- matrix-foam / device edge / online sensorium 等后续结构

CTC 轨迹最初只是投影到旧底层，用来检验旧底层是否能解释真实运动。v2.6 才开始生成 shadow bottom。

## 12. P/R/Xi 的修正定义

用户补充指出：P/R 本身不应只是分数，而应是一种跨时空窗口中的“长度”占据、一类时空测度、等效概率。P 同时提供注意力让渡，使系统把算例/计算资源分配给 R、masking、Xi 与递归流程。R 可以是跨时空窗口中隐性稳定的反结构。Xi 可能是外部熵账本对账下的必要存在。

因此新的定义应为：

```text
P = 正向稳定占据测度 + 等效概率 + 注意力让渡许可
R = 结构性反占据 / 竞争解释 / 遮蔽暴露 / 外部熵冲突
Xi = P/R/屏蔽/外部熵账本对账后仍不可归类但不能丢弃的残余存储面
```

形式上：

```text
Y_k = P_k + R_k + Xi_k + epsilon_num + epsilon_ext
```

其中 `Y_k` 是当前窗口/跨窗口的信息集合，P/R 是可解释的正向和反向时空测度，Xi 是未束残余面。

## 13. Xi 的存储面

Xi 不应该只是 `xi_watch`。它应该是跨层、跨窗口、跨通道、跨原点的 residual surface：

```text
Xi(layer, origin, window_span, support_domain, channel, evidence_path)
```

它至少包括：

- 事件残余面
- 轨迹残余面
- P/R 分解残余面
- 外部熵账本残余面
- 记忆/注意力残余面

SQLite 只应保存 Xi 的账本和索引；runtime sidecar 应保存 Xi 的场/面 payload。Xi 不能直接成为 P/R。Xi 若要回流，只能经 O candidate。

## 14. 物理场、信息轨迹场与 P/R/Xi 测度场

用户询问“场”是否等同于物理场。答案是不完全等同。

项目中至少有三类场：

1. 物理/传感场  
   例如 pressure_proxy、shear_proxy、diffusion_proxy、phase、field_energy_proxy。它接近物理场，但当前仍是 proxy。

2. 信息轨迹场  
   例如 trace_density、motion_occupancy、phase_coherence。它表示哪些时空位置存在连续信息结构。

3. P/R/Xi 测度场  
   例如 P_measure(t,x,y,z)、R_measure(t,x,y,z)、Xi_residual(t,x,y,z)。它不是物理场本身，而是锚定在四维时空上的证据/测度/残余分布。

若某个场不能反投到具体时间、空间、细胞、轨迹、事件，它就是黑箱，不应进入主线。

## 15. v2.5：Evidence Reconstruction Store

v2.5 是一次关键存储升级。目标是将每个判断依据都保存为可追踪、可反投、可重放的证据链。

新增核心表：

- `information_point_v25`
- `coordinate_transform_trace_v25`
- `trajectory_window_trace_v25`
- `calculation_recipe_v25`
- `p_spacetime_measure_v25`
- `r_counter_measure_v25`
- `xi_residual_surface_v25`
- `attention_yield_event_v25`
- `decision_evidence_bundle_v25`

实际计数：

- information_point_v25 = 4575
- coordinate_transform_trace_v25 = 4575
- trajectory_window_trace_v25 = 532
- p_spacetime_measure_v25 = 532
- r_counter_measure_v25 = 532
- xi_residual_surface_v25 = 532
- decision_evidence_bundle_v25 = 532
- attention_yield_event_v25 = 262
- calculation_recipe_v25 = 7

v2.5 的意义是：真实 CTC 的每个 centroid 信息点都能追踪到原始 frame/track/x/y/area，经过归一化坐标、cell-sphere 坐标、origin-relative 坐标，再进入轨迹窗口、P/R/Xi 测度、recipe、evidence bundle。

## 16. v2.6：Shadow Cell-Sphere Reconstruction

v2.6 不是继续把真实 CTC 贴到旧底层上，而是生成旁路 shadow cell-sphere。它仍不改写原底层事实：

- 不改写 `spacetime_cell`
- 不改写 `information_fiber`
- 不改写 `raw_event_stream`
- 不改写旧 P/R/Xi source facts

新增核心表：

- `shadow_cell_identity_v26`
- `shadow_spacetime_cell_v26`
- `shadow_cell_sphere_mapping_v26`
- `shadow_cell_motion_state_v26`
- `shadow_graph_edge_v26`
- `shadow_pr_xi_comparison_v26`
- `shadow_decision_evidence_bridge_v26`

实际完整 runtime sidecar 计数：

- shadow_cell_identity_v26.jsonl = 86
- shadow_spacetime_cell_v26.jsonl = 4575
- shadow_cell_motion_state_v26.jsonl = 532
- shadow_graph_edge_v26.jsonl = 8846
- shadow_pr_xi_comparison_v26.jsonl = 532
- shadow_decision_evidence_bridge_v26.jsonl = 532

SQLite DB 作为 ledger/index，部分详细 payload 在 runtime_store/v26 JSONL sidecars 中。这个版本回答：真实 CTC 数据如果生成一个旁路底层，它会长成什么样？

## 17. 当前下载与包体问题

用户指出 v2.5/v2.6 full 包过大，small complete 和 manifest 下载也不稳定。原因包括：

- 包中包含完整历史工程树；
- 包含真实 CTC 源 ZIP；
- 包含 runtime sidecars；
- 某些输出曾是 overlay/层包，用户难以判断是否完整；
- 大 ZIP 在当前环境容易下载失败。

因此本文附带 v2.5/v2.6 的独立 manifest（JSON + Markdown），不再强迫依赖巨大包下载。manifest 记录 DB、sidecar、关键表、哈希和重建路径。后续更合理的交付方式应是：核心代码包 + DB 包 + runtime sidecar 包 + 原始数据包 + manifest + 本地重组脚本。

## 18. 上层降级为审计层后的理想架构

未来真正的类神经 runtime 不应直接由 P/R/Xi 表运行。P/R/Xi 应成为审计层、测度层和调度层。

未来架构应为：

```text
类神经 runtime:
  event field
  trace field
  activation field
  memory field
  synaptic/device edge state
  attention request field
  residual surface field

审计层:
  trace/O -> P/R -> masking -> entropy ledger -> Xi
```

P/R/Xi 可以提供受限反馈：

- P -> attention yield
- R -> counterstructure exploration request
- Xi -> residual attention request
- entropy ledger -> calibration warning

但反馈只能调节采样密度、注意力分配、边增益、记忆窗口、重放优先级；不能改写 source facts。

## 19. 下一步建议

在 v2.5/v2.6 之后，不应急着堆更多外部数据。建议先做：

```text
v2.7 Measure Field Materialization + Reversible Query Interface
```

目标：

- 将 v2.5 的 P/R/Xi 测度从 JSONL payload 升级为真正可查询的四维 measure field。
- 为每个 `p_measure_id`、`r_measure_id`、`xi_surface_id` 建立反投查询：返回对应 frame、track、point、cell、t,x,y,z。
- 提供 CLI：`explain_decision --id p25_xxx`。
- 提供 CLI：`reproject_xi --id xi25_xxx`。
- 提供 CLI：`trace_point --point-id ip25_xxx`。
- 进一步明确哪些字段属于 runtime field，哪些属于 audit ledger，哪些属于 summary report。

只有完成这一步，上层才真正可以降级为审计层，而底层和类神经结构才有足够干净、可追踪的原料。

## 20. 最后总结

当前项目最重要的变化不是“又多了几个版本”，而是项目方向已经从早期的审计诊断表，逐步转向：

```text
真实数据源
  -> 原始点集
  -> 坐标变换链
  -> 四维时空轨迹
  -> P/R/Xi 测度
  -> Xi 残余存储面
  -> shadow bottom
  -> 未来类神经 runtime 原料
```

v2.5 和 v2.6 的真正意义在于：

- v2.5 让每个判断有可追踪证据链。
- v2.6 让真实数据可以生成旁路细胞球，而不是只贴到旧底层。

接下来最重要的不是再做漂亮的报告，而是把可逆向查询、四维测度场和类神经 runtime 的输入接口稳定下来。


# 附录 A：v2.5 Manifest 摘要

# evidence_reconstruction_store_v2.5 Manifest

Generated: `2026-05-02T17:41:04.325532Z`

## Purpose
Store every judgment basis as traceable evidence: real CTC information points, coordinate transformations, trajectory windows, P/R/Xi spacetime measures, calculation recipes, and evidence bundles.

## Database
- Path: `morphosphere_evidence_reconstruction_v25_output_database.db`
- Size: 22.195 MB
- SHA256: `a9084e54e45ff82a5df4519fbba8ae1f87c42ca636bb545f317d4f0daee03b9a`
- SQLite quick_check: `ok`
- Table count: 350

## Key SQLite tables and counts
| table | rows |
|---|---:|
| `information_point_v25` | 4575 |
| `coordinate_transform_trace_v25` | 4575 |
| `trajectory_window_trace_v25` | 532 |
| `calculation_recipe_v25` | 7 |
| `p_spacetime_measure_v25` | 532 |
| `r_counter_measure_v25` | 532 |
| `xi_residual_surface_v25` | 532 |
| `attention_yield_event_v25` | 262 |
| `decision_evidence_bundle_v25` | 532 |
| `evidence_runtime_artifact_manifest_v25` | 7 |
| `evidence_source_fact_digest_v25` | 6 |
| `evidence_reconstruction_acceptance_report_v25` | 12 |
| `ctc_source_zip_provenance_v24` | 12 |
| `ctc_source_centroid_extraction_v24` | 11 |

## Runtime sidecars
| file | rows | size bytes | sha256 |
|---|---:|---:|---|
| `coordinate_transform_trace_v25.jsonl` | 4575 | 4487717 | `f1d58ec6964e9abf...` |
| `evidence_bundle_v25.jsonl` | 532 | 991335 | `3db27e74c551c2fc...` |
| `information_points_v25.jsonl` | 4575 | 3202345 | `4876a74227bc0e43...` |
| `p_measure_field_v25.jsonl` | 532 | 508510 | `60e1eff94f379248...` |
| `r_counter_field_v25.jsonl` | 532 | 529401 | `25b68ace38ed9849...` |
| `trajectory_window_trace_v25.jsonl` | 532 | 720994 | `820bb0ae69baef22...` |
| `xi_residual_surface_v25.jsonl` | 532 | 738161 | `c55f87d498969291...` |

## Package options currently present in /mnt/data
| file | exists | size MB | sha256 |
|---|---:|---:|---|
| `morphosphere_evidence_reconstruction_v25_full_package.zip` | True | 237.182 | `d612541e22c63ddf...` |
| `morphosphere_evidence_reconstruction_v25_small_complete.zip` | True | 22.011 | `e64c87c721d0574f...` |
| `morphosphere_evidence_reconstruction_v25_compact_nosource_package.zip` | True | 7.454 | `d03a468ed87920a9...` |
| `morphosphere_evidence_reconstruction_v25_compact_with_source_package.zip` | True | 63.962 | `bdf4cb1385476f8c...` |
| `morphosphere_evidence_reconstruction_v25_output_database.db.zip` | True | 5.357 | `e2ded149b3d72890...` |

## Core invariants
- source facts are not rewritten
- P/R before Xi is preserved
- Xi reentry policy is via_o_candidate_only
- SQLite is a ledger/index; runtime sidecars hold evidence payloads
- each P/R/Xi judgment has source point references and a calculation recipe reference

## Recommended local reconstruction
Download the database and this manifest first. If large ZIP downloads fail, preserve the DB plus runtime sidecar files listed above. The DB is the audit ledger; the sidecars are the runtime evidence payloads.

# 附录 B：v2.6 Manifest 摘要

# shadow_cellsphere_reconstruction_v2.6 Manifest

Generated: `2026-05-02T17:41:06.092262Z`

## Purpose
Build a shadow cell-sphere from true CTC evidence without rewriting the original bottom layer, then compare shadow motion states with P/R/Xi evidence.

## Database
- Path: `morphosphere_shadow_reconstruction_v26_output_database.db`
- Size: 27.969 MB
- SHA256: `4c6761125cb358fadaab625490092f458bed1bab5b0717bb1eacabc5e373f346`
- SQLite quick_check: `ok`
- Table count: 362

## Key SQLite tables and counts
| table | rows |
|---|---:|
| `shadow_cell_identity_v26` | 86 |
| `shadow_spacetime_cell_v26` | 4575 |
| `shadow_cell_sphere_mapping_v26` | 4575 |
| `shadow_cell_motion_state_v26` | 1 |
| `shadow_graph_edge_v26` | 8846 |
| `shadow_pr_xi_comparison_v26` | 1 |
| `shadow_decision_evidence_bridge_v26` | 1 |
| `shadow_reconstruction_metric_v26` | 8 |
| `shadow_runtime_artifact_manifest_v26` | 8 |
| `shadow_source_fact_digest_v26` | 9 |
| `shadow_reconstruction_acceptance_report_v26` | 11 |

## Runtime sidecars
| file | rows | size bytes | sha256 |
|---|---:|---:|---|
| `shadow_cell_identity_v26.jsonl` | 86 | 361575 | `6bab9fc4e3f9adb8...` |
| `shadow_cell_motion_state_v26.jsonl` | 532 | 687056 | `8d134a32136c6cae...` |
| `shadow_decision_evidence_bridge_v26.jsonl` | 532 | 839295 | `f61275fbecfbd45d...` |
| `shadow_graph_edge_v26.jsonl` | 8846 | 4825056 | `9b64f7e6b185e94b...` |
| `shadow_pr_xi_comparison_v26.jsonl` | 532 | 426781 | `235085171e40f5c3...` |
| `shadow_spacetime_cell_v26.jsonl` | 4575 | 4472660 | `06310689eb7da502...` |

## Package options currently present in /mnt/data
| file | exists | size MB | sha256 |
|---|---:|---:|---|
| `morphosphere_shadow_reconstruction_v26_full_package.zip` | True | 45.95 | `9e4fb1f7549a70bb...` |
| `morphosphere_shadow_reconstruction_v26_small_complete.zip` | True | 34.14 | `7dc46068ccd841f9...` |
| `morphosphere_shadow_reconstruction_v26_compact_nosource_package.zip` | True | 9.782 | `a3dc2b74ddb65236...` |
| `morphosphere_shadow_reconstruction_v26_compact_with_source_package.zip` | True | 66.291 | `587055ddbf44e8f4...` |
| `morphosphere_shadow_reconstruction_v26_output_database.db.zip` | True | 6.384 | `b1b6727a4b83342e...` |

## Core invariants
- original spacetime_cell/information_fiber/raw_event_stream are not overwritten
- shadow cells are derived from CTC tracks and v2.5 evidence
- shadow state is traceable back to information_point_v25 and coordinate_transform_trace_v25
- P/R before Xi is preserved
- Xi reentry policy is via_o_candidate_only

## Note on DB vs sidecar counts
The v2.6 SQLite DB is a ledger/index. Some detailed shadow tables may store representative rows or indexes, while full detailed payloads live in runtime_store/v26 JSONL sidecars. Use the sidecar row counts for full runtime payload size.

## Recommended local reconstruction
Download the database and this manifest first. If large ZIP downloads fail, preserve the DB plus runtime sidecar files listed above. The DB is the audit ledger; the sidecars are the runtime evidence payloads.