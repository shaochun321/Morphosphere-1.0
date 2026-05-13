# 诺特—熵外部总账（Noether–Entropy External Ledger）

> See `morphosphere_total_rules_v7_final.md` Section 4 for full details.

该总账是一个**外部伴随总账层**：
- 不进入主链的状态更新方程；
- 与系统时钟、分析窗口、transport、对象冻结链并行运行；
- 记录守恒账、熵账、耗散账、异常账、噪声预算账；
- 为 replay / shell0 / archive alignment / hard cases 提供统一对账基准。

## 三本并行总账
1. **物理账 (PhysicalLedger)**: `Delta E_modeled = W_ext + Q_in - Q_out - D_explicit + R_unmodeled`
2. **信息账 (InformationLedger)**: `I(T_k) + N_k = I(P_k) + I(R_k) + L_k + A_k`
3. **外部熵账 (ExternalEntropyLedger)**: `Sigma_ext = Sigma_transport + Sigma_fragment + Sigma_boundary + Sigma_noise`

## 外部自由能：统一货币，但不偷换现实
`F_ext(m) = U_struct(m) - tau * H_ext(m)`

只用于解释：
- 前后总量为什么变了
- 变大是不是合法源项
- 变小是不是粗粒化 / 边界 / 数值耗散
- 哪些仍解释不掉，必须挂异常账
