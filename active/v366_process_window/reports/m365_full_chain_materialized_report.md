# Morphosphere v36.5 Full-Chain Materialized Data Run
**性质**：离线全链路数据实化索引，不是在线生命 runtime，也不是单纯 validation。
## 1. 结论
本次已生成 `m365_full_chain_materialized.db`，用 `m34.db` 作为底层已实现数据底座，并把 v35、v35H、v36.2、v36.3、v36.4、v36.5 的 overlay/sidecar 数据挂入同一物化索引。
新增的两层已经显式落表：
- `information_point_3d4d_backprojection`：信息点三维/四维回投层。
- `counter_evidence_chain_materialized` + `masking_layer_materialized`：反证链与屏蔽层。

## 2. 使用的 DB 不是小 rebase DB，而是全量 base + overlay
- `base_m34`: 88.71 MB
- `m25`: 26.32 MB
- `m26`: 30.82 MB
- `m35`: 0.25 MB
- `m35H`: 0.26 MB
- `m362`: 0.18 MB
- `m363`: 0.21 MB
- `m364`: 0.25 MB
- `m365`: 0.21 MB
- `rebase`: 0.04 MB

## 3. 关键物化对象计数
| 层 | 物化行数 |
|---|---:|
| source_data | 1 |
| information_point | 4575 |
| information_point_3d4d_backprojection | 4575 |
| information_point_to_trajectory | 13941 |
| trajectory_to_o_pr_r_xin | 532 |
| counter_evidence_chain | 532 |
| masking_layer | 52 |
| preneural | 50 |
| external_entropy_ledger | 4489 |
| attention | 120 |
| hyperedge | 120 |
| hyperedge_incidence | 855 |
| variational_path | 120 |
| spacetime_band_coupler | 210 |
| xin_carrier_external_readout | 31 |

## 4. 两个新增层的解释
### 4.1 信息点三维/四维回投层
该层把 `information_point_v25` 与 `coordinate_transform_trace_v25`、`spacetime_cell` 合并，保存 time、raw xyz、normalized xyz、cell-sphere xyz、nearest spacetime cell、origin anchor、relative xyz、transform error 和 reversible refs。当前源是 2D CTC，因此 z 多数为 0；但表结构保留 t+x+y+z 的 4D schema，并记录 `z0_for_2d_source` 的降级事实。
### 4.2 反证链与屏蔽层
该层把 `r_counter_measure_v25` 物化为 `counter_evidence_chain_materialized`，并把早期 `masking_counterevidence_record` 与 v35 `v35_masking_proposal` 合并为 `masking_layer_materialized`。这让 R 不是普通 residual，而是可追踪的反证链；masking 也不是删除，而是屏蔽/鲁棒性测试记录。

## 5. 完整性审计
| Audit | Scope | Status | Observed | Expected | Blocking |
|---|---|---|---:|---|---:|
| audit_001_information_points | source | PASS | 4575 | >0 | 1 |
| audit_002_3d4d_backprojection | information_point_3d4d_backprojection | PASS | 4575/4575 | one transform per information point | 0 |
| audit_003_point_to_trajectory | trajectory | PASS | 13941 | > information point count due sliding windows | 0 |
| audit_004_pr_xin_decisions | O/P/R/Xin | PASS | 532 | 532 | 0 |
| audit_005_counter_evidence | counter_evidence_chain | PASS | 532 | >0 | 1 |
| audit_006_masking_layer | masking_layer | PASS | 52 | >0 | 1 |
| audit_007_external_entropy | external_entropy_ledger | PASS | 4489 | >0 | 1 |
| audit_008_attention | attention | PASS | 120 | 120 | 0 |
| audit_009_hyperedge_arity | hyperedge | PASS | 7.125 | >=3 | 0 |
| audit_010_semantic_backwrite | v36.5 | PASS | 0 | 0 writes_mainline | 1 |
| audit_011_direct_upper_fk | cross_layer | WARN | upper overlay refs are stage-level/synthetic in places | direct FK from v35H/v36.x to v25 raw points | 0 |

## 6. 诚实边界
- 底层 v25/v34 的 evidence → coordinate → trajectory → P/R/Xin → evidence bundle 是精确物化链。
- v35-v36.5 的 overlay 已物化为上层治理/sidecar/读出链。部分上层对象与底层 source point 之间没有直接 FK，只能通过阶段级引用、carrier/source refs 和 sample trace 挂接。
- 这不是在线生命 runtime；它是一次离线全链路实化数据索引。
- 下一步应新增 `process_window` 和 `hypernode_spacetime_backprojection`，把 v35H/v36.x 的上层对象直接回投到底层 information point / spacetime cell。

## 7. 输出
- Materialized DB: `m365_full_chain_materialized.db`
- JSON summary and CSV inventories are generated next to the DB.
