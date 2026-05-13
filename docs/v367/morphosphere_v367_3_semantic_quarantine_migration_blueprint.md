# Morphosphere v36.7.3 Semantic Quarantine Migration 蓝图

## 版本定位

`v36.7.3_semantic_quarantine_migration`

目标是把 Pass17/Pass18 中识别出的主线相邻解释性文本字段迁移到只读 sidecar / readout mapping，并为核心计算路径提供 semantic-free view manifest。

## 原则

- 不破坏性改写 legacy DB。
- 主线计算路径只使用 ID、hash、numeric measure、timestamp、ledger ref。
- readout/report/test 文本允许存在，但必须只读，不能进入 P/R/Xin truth 或 source facts。
- semantic_write_allowed = 0。

## 核心表

```text
v3673_semantic_quarantine_sidecar
v3673_text_field_migration_audit
v3673_mainline_semantic_free_view_manifest
v3673_core_text_risk_resolution
v3673_allowed_text_surface
v3673_semantic_backwrite_regression
v3673_full_chain_trace_semantic_residue_audit
v3673_acceptance_report
```

## 验收标准

```text
quarantine_sidecar_rows >= 36
legacy destructive mutation = 0
semantic_write_allowed = 0
semantic backwrite regression PASS
sample full-chain traces expose no mainline semantic payload
```
