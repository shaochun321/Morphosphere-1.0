# 跨层变换宪法（Transformation Constitution）

> See `morphosphere_total_rules_v7_final.md` Section 3 for full details.

本宪法规定不同层使用不同数理体系时，哪些量可以变、怎么变、保留什么、丢掉什么、误差怎么算、回指如何保持、什么绝对不允许跨层直接抽取。

## 量类分层
- `physical_quantities`
- `hybrid_signal_summaries`
- `structural_field_quantities`
- `frozen_object_quantities`
- `semantic_projection_quantities`
- `external_diagnostic_quantities`

## 五类合法变换
1. `state_preserving_lift` (视图变化但不改变本体语义)
2. `coarse_graining_summary` (受约束的粗粒化摘要)
3. `structural_encoding` (把点集 / 窗口对象编码成图、场、矩阵、tensor，但不改变本体)
4. `object_freezing` (从候选域冻结对象)
5. `read_only_projection` (单向投影)

## 三条红线
1. 不得出现无来源单位的中间量成为主链依据。
2. 不得出现不同层各自维护自己的总量。
3. 不得出现未登记的跨层偷桥。

所有变换必须登记在 `data_contracts/transform_registry.yaml` 中。
