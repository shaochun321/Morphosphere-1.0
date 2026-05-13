# Morphosphere v36.7.1 蓝图：Native Anchor Hardening

## 版本定位

`v36_7_1_native_anchor_hardening`

## 核心目标

把 Pass20/Pass21 已经验证的 writer-emitted facts 固化为 **v36.7.1 原生锚定基线**，但不篡改旧 DB 中 `direct_fk_available = 0` 的历史事实。

## 背景约束

- v36.7 硬化路线要求不新增理论对象，而是把已验证的硬外键、安全应力包络、RMI、语义隔离固化为工程基线。
- v37 方向中的 Native Process Writer / Dark Grid / RMI 可以作为后续目标，但当前阶段不能直接宣称 Online Native Runtime。

## 设计原则

1. 历史诚实：legacy `v366_hypernode_spacetime_backprojection.direct_fk_available` 保持原样。
2. 新增事实层：建立新的 `v367_native_anchor_fact`，记录 writer-emitted anchor。
3. 全量覆盖：覆盖 855 条 hypernode / writer facts。
4. 硬锚定字段：每条 anchor 绑定 information point、trajectory window、evidence bundle、coordinate transform、P/R/Xi、ledger、dark-grid zone、hash。
5. 不宣称在线 runtime：本版本是 native anchor baseline，不是 100ms online coordinate audit，也不是在线原生生命 runtime。

## 核心表

```text
v367_native_anchor_fact
v367_process_window_fk_binding
v367_hypernode_native_backprojection
v367_dark_grid_zone_index
v367_anchor_validation_result
v367_legacy_directness_comparison
v367_coordinate_invariance_regression
v367_regression_gate
v367_acceptance_report
```

## 验收标准

```text
native_anchor_fact rows = 855
information_point_ref hit = 855 / 855
trajectory_window_ref hit = 855 / 855
evidence_bundle_ref hit = 855 / 855
operational ledger ref = 855 / 855
legacy direct_fk_available remains 0
coordinate invariance CI = PASS
semantic_write_allowed = 0
```

生成时间：2026-05-06T18:54:54.859817+00:00
