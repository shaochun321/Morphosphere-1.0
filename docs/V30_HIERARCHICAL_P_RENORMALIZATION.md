# Morphosphere v30 实施报告：Hierarchical P Renormalization

## 定位

v30 将 v28 的 confirmed P 与 v29 的 sandbox intervention effect 结合，生成候选宏观节点（macro-node candidate）。它不是行动系统，也不让宏观节点成为 source truth。

## 核心边界

- source facts rewritten = 0
- hot swap allowed = 0
- macro nodes active as source = 0
- Xi direct to P/R = 0
- 宏观节点只是候选，不改写 Evidence / Shadow / P/R/Xi

## 主要输出计数

| table | rows |
|---|---:|
| `v30_confirmed_p_cluster` | 59 |
| `v30_effective_information_probe` | 160 |
| `v30_macro_node_candidate` | 1 |
| `v30_hierarchical_edge` | 25 |
| `v30_cross_level_attention_request` | 1 |
| `v30_macro_node_lineage` | 1 |
| `v30_acceptance_report` | 12 |

## 已实施

1. `v30_confirmed_p_cluster`：按 source track 聚合稳定 confirmed P。
2. `v30_effective_information_probe`：吸收 v29 sandbox 的 effective information proxy。
3. `v30_macro_node_candidate`：生成候选宏观节点。
4. `v30_hierarchical_edge`：记录 macro-node 到 confirmed P 子结构的边。
5. `v30_cross_level_attention_request`：允许宏观节点发出 attention request，但不允许修改事实。
6. `v30_macro_node_lineage`：记录宏观节点从 v25-v29 的血缘。

## 悬置

- EI 仍是 proxy，不是严格因果干预信息。
- macro-node 还不能作为真正 runtime substrate。
- 尚未把 macro-node 回灌到新的高层 O/P/R/Xi 循环。
- 尚未接入真实多源 bottom prediction adapter。

## 本地运行

```bash
unzip Morphosphere_v30.zip
cd Morphosphere_v30
./CHECK_BASELINE.sh
./RUN_EXAMPLES.sh
```
