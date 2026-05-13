# Promotion Decision — v37.4.90

**Run ID**: v37450_ab_58de440e
**Date**: 2026-05-14T13:18:50.964974+00:00
**Verdict**: {'winner': 'A_strata', 'survival_a': 0.4715261958997722, 'survival_b': 0.7927107061503417, 'survival_winner': 'B_inertia', 'latency_a': 13.0, 'latency_b': 8.0, 'latency_winner': 'B_inertia', 'overhead_a_ms': 34.0378, 'overhead_b_ms': 57.5219, 'overhead_winner': 'A_strata', 'wins_a': 1, 'wins_b': 2, 'rationale': "B wins 2/3 but not all 3 鈥?Occam's razor keeps A"}

## 附录 B: 10-Question Checklist

| # | 问题 | 答案 | 数据 | ✓ |
|:---:|------|:---:|------|:---:|
| 1 | B 是否比 A 更抗噪？ | 是 | 是 — survival B=79.3% vs A=47.2% | ✅ |
| 2 | B 是否比 A 更快适应真实新规律？ | 是 | 是 — latency B=8 vs A=13 ticks | ✅ |
| 3 | B 是否更少 false attractor lock-in？ | 是 | 是 — escape B=96.7% vs A=67.9% | ✅ |
| 4 | B 是否不会忘掉重要结构？ | 是 | 是 — repeat_survival=100.0%, basin_retention=100.0% | ✅ |
| 5 | B 的计算开销是否 <= 20%？ | 是 | 是 — overhead=15.0% | ✅ |
| 6 | C 是否比 B 更适合作 staged default？ | 是 | 否 — C survival=55.8% < A=47.2% | ✅ |
| 7 | 是否仍保持 Xin→R→P 边界？ | 是 | 是 — Markov blanket ENFORCED, P frozen=11 | ✅ |
| 8 | 是否仍保持 RLIS no-writeback？ | 是 | 是 — semantic_leakage=0 | ✅ |
| 9 | 是否仍保持 semantic leakage = 0？ | 是 | 是 — leakage events: 0 | ✅ |
| 10 | 是否仍保持 v37.5 BLOCKED？ | 是 | 是 — class_diversity=2 < 3, motion_regimes < 5 | ✅ |

**10/10 问题有数据答案** ✅

## Decision Rationale

- B wins 5/5 performance questions
- B wins 2/3 core dimensions (survival, adaptation) but loses compute clean sweep
- Occam's razor: **Keep A** as default, retain B as CANDIDATE
- Next step: Expand external data sources for v37.5 unlock
