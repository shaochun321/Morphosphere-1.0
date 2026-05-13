# Morphosphere v36.1 Variational External Ledger Bridge Overlay Report

**Artifact type:** `ENGINEERED_BRIDGE_OVERLAY`  
**Includes full base:** `false`  
**Not full lineage:** `true`  
**Created:** 2026-05-05T11:46:54.238124+00:00

## Purpose

This overlay implements the v36.1 bridge layer: **External Ledger Variational Action Proxy**. It turns the v36.1 blueprint into a runnable single-layer package without pretending to include the full v25-v34 base, v35, v35H, v36, or v36.5 overlays.

The core change is that `Delta Xin` is no longer the main definition of Xin. Delta Xin is retained only as a fallback / diagnostic / sanity check. The main object is now:

```text
S_IE_proxy[Gamma]
  -> top-k candidate path scoring
  -> stationarity_defect / EL_residual_proxy
  -> Xin_var
```

## Implemented tables

```text
v361_action_functional_registry        4
v361_candidate_path_inventory        120
v361_external_ledger_lagrangian_proxy 120
v361_variational_metric_state        120
v361_stationarity_defect             120
v361_xin_variational_defect          120
v361_delta_xin_fallback_snapshot     120
v361_action_scoring_report           120
v361_downgrade_contract                8
v361_acceptance_report                12 / 12 PASS
```

## Boundary conditions

```text
source_facts_rewritten = 0
hot_swap_allowed = 0
semantic_label_in_mainline = 0
continuous_variational_solver_claimed = 0
physical_action_claimed = 0
delta_xin_as_main_definition = 0
xin_direct_to_P_allowed = 0
xin_direct_to_R_allowed = 0
raw_coordinate_replaced = 0
```

## Downgrade / minimization / revision

| Original philosophy / math | Downgraded engineering object | Minimization / revision |
|---|---|---|
| Continuous action functional | `S_IE_proxy[Gamma]` | Discrete top-k candidate path scoring |
| `delta S = 0` | `stationarity_defect` | Local residual estimate, not analytic solve |
| Euler-Lagrange equation | `EL_residual_proxy` | Neighbor-window / candidate perturbation residual |
| Differential Xin field | `Xin_var` | Variational non-closure projection |
| Minimum action path | `top_k_path_selection` | Sandbox ranking, not global solve |
| Information-energy spacetime metric | `provisional_variational_metric_proxy` | Bounded update with raw-coordinate guard |
| External ledger Lagrangian | `external_ledger_lagrangian_proxy` | Versioned registry with meta-proxy coefficients |
| Delta Xin | `delta_xin_fallback_snapshot` | Fallback / diagnostic only |

## Local run

```bash
tar --zstd -xf Morphosphere_v36_1_variational_bridge_overlay.tar.zst
cd Morphosphere_v36_1_variational_bridge_overlay
./RUN_EXAMPLES.sh
python3 active/v361/scripts/check_v361.py --db outputs/m361.db
python3 active/v361/scripts/query_v361.py --db outputs/m361.db --limit 5
python3 active/v361/scripts/audit_v361_action.py --db outputs/m361.db
```

## Apply to existing tree

```bash
./APPLY_TO_EXISTING_TREE.sh /path/to/Morphosphere_tree
```

## Notes

This overlay is intentionally small and does not include the full base. A later cumulative bridge rollup will include v35, v35H, v36, and v36.1 together so that single-layer download failures do not break the lineage.
