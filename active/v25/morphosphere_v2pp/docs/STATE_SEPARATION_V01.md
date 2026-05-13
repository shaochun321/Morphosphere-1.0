# STATE_SEPARATION_V0.1 说明

## 为什么加入这一层

当前 v8.5.3 已经能产生异质底层信号、transport、O/P/R/Xi 诊断账本和扰动报告，但旧链路仍然有一个关键不足：它能记录候选结构，却不能充分证明候选结构是从无语义时空数据中被分离出来的。

`state_separation_v0.1` 的目标是把项目理念向前推一步：

```text
信息结构先由时空结构出来；
之后才允许尝试在信息结构中反向计算时空。
```

因此，这一层只读取：

```text
spacetime_cell
information_fiber
```

它不读取：

```text
object_hypothesis
o_candidate_record
pr_confirmation_graph_record
semantic_readout
```

## 核心链路

```text
spacetime_cell + information_fiber
  -> raw_event_stream
  -> origin_anchor
  -> latent_trajectory
  -> trajectory_event_binding
  -> xin_residue_state
  -> trajectory_reprojection_report
```

## 概念对应

| 项目理念 | 本构建中的落地 |
|---|---|
| 新原点 | `origin_anchor` |
| 无语义输入事件 | `raw_event_stream` |
| T / Trace | latent trajectory 的 centroid / velocity / phase path |
| O 的前身 | `latent_trajectory`，不是语义 object |
| P/R 的前身 | continuity / conservation / phase / reprojection tests |
| Xi / Xin | `xin_residue_state` |
| 回投到底层 3D 细胞球 | `trajectory_reprojection_report` |

## 这次构建回答的问题

它尝试回答：

```text
1. 不贴标签时，底层时空事件能否被分解成多条轨迹？
2. 5-10% 噪声下，轨迹分配是否不会崩溃？
3. 20-30% 噪声下，Xin residual 是否增加？
4. 人为隐藏注入一个低频连续结构时，系统是否能把它识别为新 proto structure？
5. 不同 channel type 是否能靠相位/连续性绑定，而不是靠语义绑定？
6. latent trajectory 是否能部分回投到底层 3D 细胞球状态？
```

## 本地运行

从工程包根目录运行：

```bash
./run_local_state_separation.sh
```

或进入 `morphosphere_v2pp` 后运行：

```bash
python -S scripts/run_state_separation_acceptance.py ../outputs/morphosphere_state_separation_v01_output_database.db
```

重新生成 state-separation 层：

```bash
python -S scripts/run_state_separation_core.py --db ../outputs/morphosphere_state_separation_v01_output_database.db
```

## 禁止解释

本层输出禁止被解释为：

```text
已经涌现语义
已经形成真实意识
已经完成真实生物学
已经证明真实物理模型
```

它只能说明：在当前诊断数据上，项目已经开始具备“无语义时空状态分离”的最小测试链路。
