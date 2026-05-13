# Morphosphere Context Compaction v36.6

Generated: `2026-05-06T03:09:14Z`

## 1. 本轮对话压缩结论

本轮确认：Morphosphere 的大层级基本没有变化，变化的是每层实现形态、数据入口、存储系统和链路是否被绕过。Stage 1 / Stage 2 不是丢失，而是经历多轮重构后不再总以旧目录名出现。

用户纠偏的核心点：Stage 1 是底层机电细胞球球体；当前同级接入了 2D 外部下载真实数据。前神经层与接口束属于 Stage 1 和 Stage 2 类神经系统共有。Stage 2 目前可能被部分架空，信息链路存在 evidence -> trajectory -> P/R/Xin 的绕行路径。

## 2. 项目大层级标注

| 层级 | 名称 | 理论身份 | 当前状态 |
|---|---|---|---|
| 0 | External Input / Reality Envelope | 外部真实源、下载数据、模拟源、传感源。当前以 CTC 2D 真实细胞运动数据为主要真实输入。 | 已有真实数据入口；不是完整 3D 机电细胞球。 |
| 1 | Stage 1 Physical / Source Substrate | 底层机电细胞球 / 物理源事实层。包含 spacetime_cell、information fiber、机电/泡沫/基质代理。 | 理论层未变；实现经历 legacy physical loop、source boundary、2D 外部源同级替代。 |
| 1.5 | Preneural / Interface Bundle | Stage 1 与 Stage 2 共有接口束：raw event、information_fiber、preneural carrier、transport/afferent/device-neutral edge。 | 存在但在最新 materialized chain 中不够显式，需要 operator trace 化。 |
| 2 | Stage 2 Object Surface / Candidate Machinery | 对象表面、O candidate、P/R candidate machinery、SPMS、confirmation graph。 | 理论存在；当前可能被 evidence -> trajectory -> P/R/Xin 直接路径部分绕过。 |
| 3 | T/O/P/R/Xin Core Recursion | Trace/Transport -> O -> P/R -> masking / counter-evidence -> Xi。 | 项目中轴不变；P/R 不能被 Xin 顶替，Xi 只能经 O-candidate re-entry。 |
| 4 | Information Point 3D/4D Backprojection | 信息点三维/四维回投：information point -> raw/normalized/cell-sphere/origin-relative coordinate -> trajectory window。 | 已物化 4575 行；2D 数据以 z=0 进入 4D schema。 |
| 5 | Counter-evidence and Masking Layer | 反证链、屏蔽层、precision gate、attention competition、Xi momentum/appeal。 | 已在 materialized DB 中物化 counter-evidence 与 masking；v35/v35H 继续高阶化。 |
| 6 | Storage and Materialization System | 从单纯 SQL 演化为 SQLite ledger/index/audit + runtime_store payload + sparse incidence sidecar + full-chain materialized index。 | 当前关键是建立 object lineage，而不是只跑 validation。 |
| 7 | External Entropy / Proxy Governance | 外部熵账本、proxy/meta-proxy、Noether-style audit、runtime guard。 | 裁判层，不是本体层；不能反写 source facts 或 P/R/Xi。 |
| 8 | Attention / Hypergraph / Variational Upper Layers | v35 attention、v35H incidence、v36.x variational/R-band/coupler、v36.5 Xin carrier/readout。 | 已有 overlay 数据；与底层直接 FK 仍需 v36.6 回投骨架。 |
| 9 | v36.6 Process Window Layer | 新主线工作单位：information/time/support/process/envelope/ledger。 | 本轮已新增 m366_process_window.db。 |
| 10 | v36.6 Hypernode Spacetime Backprojection | v35H hypernode/hyperedge 到 information point / trajectory / spacetime cell / P/R/Xi 的回投审计索引。 | 本轮已新增；目前 855 条均标记为 proxy/inferred，不伪装成 direct FK。 |

## 3. 存储系统演化

早期存储更接近单一 SQLite/diagnostic tables；随后 SQLite 同时承担 runtime 与 audit，开始膨胀；之后 runtime_store 与 SQLite ledger 分离；v25/v26 以后 SQLite 更像 ledger/index，JSONL/runtime_store 承担 payload；v35H 后高阶关系采用 sparse incidence sidecar；当前增加 full-chain materialized index 与 v36.6 process_window index。

当前存储分工：

- source archive：原始输入、hash、来源声明。
- runtime_store sidecar：大 payload、场、轨迹、JSONL。
- per-version SQLite：ledger、index、manifest、acceptance、audit。
- sparse incidence sidecar：逻辑超图的 COO/稀疏索引。
- full-chain materialized index：跨层数据索引，不等同于 validation。
- v36.6 process_window index：过程窗口与 hypernode 回投审计骨架。

## 4. v36.6 本轮新增产物

本轮新增 `m366_process_window.db`，它不修改任何旧 DB，只作为 additive materialized index。

| 指标 | 数值 |
|---|---:|
| `process_window_count` | 1133 |
| `trajectory_process_windows` | 532 |
| `attention_process_windows` | 120 |
| `hyperedge_process_windows` | 120 |
| `variational_process_windows` | 120 |
| `band_coupler_process_windows` | 210 |
| `xin_carrier_process_windows` | 31 |
| `process_window_member_count` | 20128 |
| `hypernode_backprojection_count` | 855 |
| `hyperedge_relation_count` | 2625 |
| `coordinate_nonlocal_relation_count` | 1682 |
| `coordinate_nonlocal_audit_examples` | 50 |
| `proxy_hypernode_backprojection_count` | 855 |

边界：`hypernode_spacetime_backprojection` 当前大多是 proxy/inferred，因为 v35H overlay 没有完整硬 FK 指向 v25-v34 evidence 表。DB 已显式保存 `direct_fk_available=0`，避免把代理回投伪装成直接事实。

## 5. process_window 应构建在哪里

建议位置：`active/v366_process_window/db/m366_process_window.db`，并在 full-chain materialized DB 中保留同步索引。它读取 v25-v36.5 的已实现数据，生成 v36.6 的主线窗口索引。

`process_window` 的职责：绑定 information payload、time span/order、support domain、process operator trace、external input envelope、external ledger balance ref。它不是对象、不是语义事件、不是坐标盒子。坐标从主线解释中隐去，但保留为 raw coordinate audit。

## 6. hypernode_spacetime_backprojection 应构建在哪里

建议与 process_window 同级构建，不塞回 v35H。v35H 只负责逻辑超图 incidence；v36.6 回投层负责把 hypernode/hyperedge 反投到 information point、trajectory window、spacetime cell、coordinate transform、P/R/Xi measure。

核心字段必须包括：hypernode_id、hyperedge_id、source_table/source_ref、information_point_ref、trajectory_window_ref、spacetime_cell_ref、coordinate_transform_ref、p/r/xi refs、t/x/y/z、projection_confidence、resolution_method、direct_fk_available、audit_status。

## 7. 下一步建议

1. 把 v36.6 表写入工程树 `active/v366_process_window`，补 `build_process_window.py`、`check_process_window.py`。
2. 针对 Stage 2 被绕过的问题，增加 `stage2_object_surface_materialization_audit`。
3. 把 preneural/interface bundle 从 summary 层提升为 operator trace 层。
4. 为 v35H hypernode 增加更硬的 source_ref 解析规则，逐步把 proxy backprojection 迁移为 direct FK。
5. 继续保持语义只读、source facts 不改写、Xin direct-to-P/R 阻断。
