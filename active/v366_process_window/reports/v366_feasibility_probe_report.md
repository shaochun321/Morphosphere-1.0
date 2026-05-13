# v36.6 Feasibility Probe from v36.5 Data

Generated: `2026-05-05T19:09:29.940253+00:00`

## Executive judgement

**Verdict:** `CONDITIONALLY_READY_FOR_V36_6_PROCESS_WINDOW`

数据支持进入 v36.6 的最小工程化阶段，但非局域证据仍需要正式 coordinate backprojection 外键来从 proxy evidence 升级为硬证据。

## 1. Hyperedge arity check

- Status: `PASS`
- Hyperedges: `120`
- Average nodes per hyperedge: `7.125`
- Min / max arity: `7` / `8`
- Hyperedges with arity < 3: `0`

Interpretation: v35H 当前不是二元图边伪装；它确实有高阶 incidence 基础，可以支撑 process window 中的多主体关系索引。

## 2. Xin carrier external definition decoupling

- Status: `PASS_WITH_LIMITATION`
- Xin carriers: `31`
- Non-null external definition refs: `31`
- Non-null ratio: `1.000`
- External definition families: `6`
- Carriers with >=3 external definitions: `0`

Interpretation: 外部定义机制没有空转，但当前数据还没有出现真正的“一 carrier 多解释复调冲突”。复调治理可以设计接口，不必马上做复杂仲裁器。

## 3. Nonlocal backprojection / coordinate deviation check

- Status: `PASS_PROXY_EVIDENCE`
- Direct v35H -> spacetime_cell FK available: `False`
- Projection method: `proxy_projection_v1_no_direct_fk`
- Projected hyperedges: `120`
- Projected node pairs: `2625`
- Distance threshold: `6.0`
- Pairs above threshold: `1984`
- Max projected distance: `10.288855`
- Top pair: `he35h_0005` / `hn35h_0070` -> `stc_0_20` and `hn35h_0138` -> `stc_8_38`

Interpretation: 找到了同一超边内的远距离投影节点对，但这是 proxy evidence，不是严格外键铁证。v36.6 的第一张新表应是 `process_window_coordinate_backprojection` 或 `hypernode_spacetime_backprojection`。

## 4. Hub / overload check

- Status: `PASS_NO_OVERLOAD`
- Objects checked: `1078`
- Overload threshold: `50`
- Overloaded objects: `0`
- Max total references: `4`
- Top ref: `xin_carrier_000` from `v362_candidate_path_inventory.xin_carrier_ref`

Interpretation: 没有超过 50 条路径/超边引用的枢纽节点；当前规模下没有 hub 黑洞。但 v36.6 扩容后仍应保留 hub cap / top-k neighborhood guard。

## Recommended v36.6 implementation gate

1. 允许做最小 `process_window` 主表。
2. 必须先补 `hypernode_spacetime_backprojection`，把本次 proxy 非局域证据升级为直接可审计 FK。
3. 不要立即建设“超级超图”；当前 arity 足够，但 polyphony 冲突不足，先做稀疏 process-window sidecar。
4. Xin 外部定义模块可以继续保持 read-only；暂时不需要复杂复调仲裁。
5. 继续禁止 source fact rewrite、semantic backwrite、Xin direct-to-P/R。

## Artifacts

- Analysis DB: `/mnt/data/v366_feasibility_probe.db`
- JSON summary: `/mnt/data/v366_feasibility_probe_summary.json`
