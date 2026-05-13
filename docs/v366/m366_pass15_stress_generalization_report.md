# Morphosphere v36.6 Pass15 — Stress and Generalization Evidence

生成时间：2026-05-06T16:26:03.788784+00:00

## 0. 定位

Pass15 不新增理论层。它针对两份外部分析提出的问题执行三类数据审计：

1. 坐标刚性平移 / 非刚性扭曲压力；
2. 结构化反证链注入；
3. CTC 01/02 不调参泛化对比。

同时补充两项审计：hypernode 回投 directness 分级、Xin 37.78% 类说法的表级复核。

边界：坐标压力从 source information points 重新计算轨迹几何；反证注入仍是 measurement-level stress projection，不是完整 source rerun；02 比较使用 m25 同流程数据，不是外部跨数据集验证。

## 1. Acceptance

| check_id   | status   | observed                                | requirement                                                          | note                                  |
|:-----------|:---------|:----------------------------------------|:---------------------------------------------------------------------|:--------------------------------------|
| A1         | PASS     | PASS                                    | rigid translation should preserve trajectory metrics and role proxy  | checks absolute coordinate dependence |
| A2         | PASS     | localized=70, global_collapse=0         | nonrigid warp should localize pressure without global collapse       | checks local stress response          |
| A3         | PASS     | 65.0/65                                 | R should increase monotonically under structured counter injection   | measurement-level pressure audit      |
| A4         | PASS     | p_core_collapse_rows=0.0/260            | P should not globally collapse under boundary counter injection      | locality check                        |
| A5         | PASS     | seq02_windows=291.0                     | CTC 02 sequence should be present for no-retune comparison           | n=1 mitigation                        |
| A6         | WARN     | raw_direct=0; normalized_candidates=390 | Backprojection directness must not be faked; raw direct remains debt | directness tiering                    |
| A7         | PASS     | Xin role denominator=532                | Xin role share must be bounded to empirical role classifier          | prevents rhetoric overclaim           |

## 2. Coordinate Stress Summary

| stress_id                     |   trajectory_count |   role_changed_count |   max_abs_rel_path_length_delta |   max_abs_delta_direction_coherence |   max_abs_delta_curvature |   localized_pressure_count |   global_collapse_flag | verdict   | interpretation                                                            |
|:------------------------------|-------------------:|---------------------:|--------------------------------:|------------------------------------:|--------------------------:|---------------------------:|-----------------------:|:----------|:--------------------------------------------------------------------------|
| C0_rigid_translation          |                520 |                    0 |                      6.1551e-15 |                          1.4988e-15 |               1.64313e-14 |                          0 |                      0 | PASS      | Rigid translation preserved recomputed trajectory metrics and role proxy. |
| C1_nonrigid_registration_warp |                520 |                   40 |                      4.33106    |                          0.738392   |               0.851414    |                         70 |                      0 | PASS      | Nonrigid warp created local metric pressure without global role collapse. |

解释：刚性平移如果改变轨迹几何或角色，说明系统依赖绝对坐标；本轮刚性平移为 PASS。非刚性扭曲产生局部压力但未全局崩溃，符合结构性扰动预期。

## 3. Counter-evidence Injection Summary

| metric                   |   value | interpretation                                                     |
|:-------------------------|--------:|:-------------------------------------------------------------------|
| target_p_stable_windows  |      65 | number of P_STABLE_SUPPORT windows used as injection targets       |
| monotonic_r_cases        |      65 | cases where R increased monotonically across injection intensities |
| r_band_triggered_rows    |     257 | stress rows satisfying R-band trigger proxy                        |
| xin_localized_rows       |     130 | stress rows where Xin increased locally above threshold            |
| p_core_collapse_rows     |       0 | rows where P fell below 50 percent of baseline; should remain low  |
| projected_role_to_R_rows |     260 | rows where projected dominant role became R_COUNTER_PRESSURE       |

解释：对 P_STABLE_SUPPORT 窗口边界施加结构化反证压力后，R 随强度单调上升；这说明 P/R 分离不是完全不可撼动的静态标签。但该测试仍是测度层压力投影，下一步应升级为 source-level rerun harness。

## 4. CTC 01/02 No-retune Role Distribution

| row_id                   |   sequence_id | role_proxy            |   window_count |     share |   mean_p |   mean_r |   mean_xin |
|:-------------------------|--------------:|:----------------------|---------------:|----------:|---------:|---------:|-----------:|
| 01_LOW_OR_MIXED_SIGNAL   |            01 | LOW_OR_MIXED_SIGNAL   |             50 | 0.207469  | 0.563492 | 0.284534 |   0.276999 |
| 01_P_R_MIXED_COMPETITION |            01 | P_R_MIXED_COMPETITION |             20 | 0.0829876 | 0.586926 | 0.304792 |   0.266224 |
| 01_P_STABLE_SUPPORT      |            01 | P_STABLE_SUPPORT      |             33 | 0.136929  | 0.603399 | 0.275614 |   0.216891 |
| 01_R_COUNTER_PRESSURE    |            01 | R_COUNTER_PRESSURE    |             26 | 0.107884  | 0.54987  | 0.335891 |   0.247666 |
| 01_XIN_RESIDUAL_PRESSURE |            01 | XIN_RESIDUAL_PRESSURE |            112 | 0.46473   | 0.564521 | 0.307485 |   0.328206 |
| 02_LOW_OR_MIXED_SIGNAL   |            02 | LOW_OR_MIXED_SIGNAL   |             87 | 0.298969  | 0.556898 | 0.28096  |   0.25516  |
| 02_P_R_MIXED_COMPETITION |            02 | P_R_MIXED_COMPETITION |             17 | 0.0584192 | 0.577353 | 0.306148 |   0.278302 |
| 02_P_STABLE_SUPPORT      |            02 | P_STABLE_SUPPORT      |             32 | 0.109966  | 0.618529 | 0.277362 |   0.228125 |
| 02_R_COUNTER_PRESSURE    |            02 | R_COUNTER_PRESSURE    |             66 | 0.226804  | 0.532606 | 0.335524 |   0.266831 |
| 02_XIN_RESIDUAL_PRESSURE |            02 | XIN_RESIDUAL_PRESSURE |             89 | 0.305842  | 0.526772 | 0.291904 |   0.304942 |

## 5. Backprojection Directness Tiering

| tier_id   | tier_name                                |   object_count |   share | evidence_source                                                | required_upgrade                                                      | note                                                           |
|:----------|:-----------------------------------------|---------------:|--------:|:---------------------------------------------------------------|:----------------------------------------------------------------------|:---------------------------------------------------------------|
| L0        | raw_inferred_backprojection              |            855 | 1       | v366_hypernode_spacetime_backprojection.direct_fk_available=0  | requires upstream writer to emit direct refs                          | current raw backprojection remains inferred/proxy              |
| L1        | normalized_materialized_direct_candidate |            390 | 0.45614 | hypernode_fk_upgrade_applied_pass2.direct_fk_available_after=1 | may be promoted only if upstream emits normalized source_ref natively | candidate directness after normalization, not original FK fact |
| L2        | native_raw_direct_backprojection         |              0 | 0       | raw direct_fk_available=1                                      | target state for future writer contracts                              | currently absent in raw v36.6 process-window backprojection    |

解释：raw direct FK 仍为 0；normalized/materialized direct candidates 不能冒充原始 direct FK。这回应了 `direct_fk_available = 0` 的问题，但不伪造硬连接。

## 6. Xin Role Claim Recheck

| row_id                | role_proxy            |   window_count |   percentage | source_table                         |   denominator | claim_allowed          | note                                                                                                                                      |
|:----------------------|:----------------------|---------------:|-------------:|:-------------------------------------|--------------:|:-----------------------|:------------------------------------------------------------------------------------------------------------------------------------------|
| XIN_RESIDUAL_PRESSURE | XIN_RESIDUAL_PRESSURE |            201 |      0.37782 | empirical_role_classification_counts |           532 | bounded_statement_only | Percentage supports residual-pressure share in this empirical role classifier; it does not prove thermodynamic dominance or physical law. |

解释：如果引用 `XIN_RESIDUAL_PRESSURE` 约 37.78%，它只能表示 empirical role classifier 下的窗口占比；不能推出“Xin 热力学霸权”或真实物理定律。

## 7. 下一步优先级

| priority_id           |   priority | action_name                                                                         | rationale                                                                         | output_db_expected                        |
|:----------------------|-----------:|:------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------|:------------------------------------------|
| P0_coord_invariance   |          0 | Keep coordinate invariance regression in CI                                         | Rigid translation is a structural invariant; any future failure blocks release    | m366_stress_coordinate_invariance.db      |
| P0_counter_rerun      |          0 | Upgrade counter injection from measurement projection to source-level rerun harness | Deep analysis identified structural counter pressure as primary P/R stress test   | m366_stress_counter_injection_rerun.db    |
| P1_ctc02_full_overlay |          1 | Generate full v35-v36.6 overlay for CTC 02, not only v25 role comparison            | Current 02 audit covers v25/TOPRXin; upper overlays remain inherited/materialized | m366_generalization_ctc02_full_overlay.db |
| P1_directness_writer  |          1 | Promote normalized direct candidates only through upstream writer changes           | Gemini analysis correctly flagged raw direct_fk_available=0; avoid fake FK        | m366_backprojection_directness_upgrade.db |
| P2_external_dataset   |          2 | After 01/02 and stress rerun, add external CTC dataset                              | Avoid confounding data adapter issues with system behavior                        | m366_generalization_cross_dataset.db      |
