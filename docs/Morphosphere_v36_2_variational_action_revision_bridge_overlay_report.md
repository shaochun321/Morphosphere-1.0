# Morphosphere v36.2 Variational Action Revision Bridge Overlay Report

**Artifact type:** `ENGINEERED_BRIDGE_OVERLAY`  
**Includes full base:** `false`  
**Not full lineage:** `true`  
**Created:** 2026-05-05T11:57:56.077436+00:00

## Purpose

This overlay implements the v36.2 bridge layer: **Variational Action Revision**. It turns the v36.2 blueprint into a runnable single-layer package without pretending to include the full v25-v34 base, v35, v35H, v36, v36.1, or v36.5 overlays.

The core correction is:

```text
Delta Xin is not the main definition.
Xin_var is the local projection of non-closure under an external-ledger action proxy.
S_IE_proxy[Gamma] is not a physical action; it is a ranked, local, auditable action-like cost.
```

## Implemented tables

```text
v362_action_functional_candidate_library       5
v362_candidate_path_inventory                120
v362_discrete_action_score                   120
v362_stationarity_defect_proxy               120
v362_xin_var_closure_defect                  120
v362_delta_xin_fallback_snapshot             120
v362_action_comparison_report                120
v362_meta_proxy_registry                      12
v362_downgrade_contract                        9
v362_acceptance_report                    12 / 12 PASS
```

## Boundary conditions

```text
source_facts_rewritten = 0
hot_swap_allowed = 0
semantic_label_in_mainline = 0
continuous_variational_solver_claimed = 0
physical_action_claimed = 0
global_action_solve_claimed = 0
xin_direct_to_P_allowed = 0
xin_direct_to_R_allowed = 0
raw_coordinate_replaced = 0
```

## Downgrade / minimization / revision

| Original philosophy / math | Downgraded engineering object | Minimization / revision |
|---|---|---|
| Continuous action functional | `S_IE_proxy[Gamma]` | Discrete local additive score over top-k candidate paths |
| `delta S = 0` | `stationarity_defect` | Finite perturbation residual, not analytic proof |
| Euler-Lagrange equation | `EL_residual_proxy` | Neighbor-window / path perturbation approximation |
| Differential Xin field | `Xin_var` | Action / ledger / constraint / anomaly non-closure projection |
| Minimum action path | `top_k_path_selection` | Sandbox ranking, not global optimum |
| Information-energy spacetime metric | `provisional_variational_metric_proxy` | Audit-only scoring, no raw-coordinate replacement |
| External ledger Lagrangian | `external_ledger_lagrangian_proxy` | Versioned candidate functional registry |
| Delta Xin | `delta_xin_fallback_snapshot` | Fallback / diagnostic / sanity check only |
| Variational free energy | `variational_free_energy_like_audit_proxy` | Comparison family, not VFE implementation |

## Suspended items

```text
strict continuous variational solve
true Euler-Lagrange PDE solver
global path-space optimization
physical action claim
Xin ontology inside mainline
semantic interpretation inside upper recursion
```

## Rejected items

```text
using action score as truth
using stationarity defect as natural law
allowing Xin_var to write P/R directly
replacing raw coordinates with information-energy metric
using Delta Xin as primary Xin definition
allowing external ledger to rewrite source facts
```

## Local run

```bash
tar --zstd -xf Morphosphere_v36_2_variational_action_revision_bridge_overlay.tar.zst
cd Morphosphere_v36_2_variational_action_revision_bridge_overlay
./RUN_EXAMPLES.sh
python3 active/v362/scripts/check_v362.py --db outputs/m362.db
python3 active/v362/scripts/query_v362.py --db outputs/m362.db --limit 5
python3 active/v362/scripts/audit_v362_action.py --db outputs/m362.db
```

## Apply to existing tree

```bash
./APPLY_TO_EXISTING_TREE.sh /path/to/Morphosphere_tree
```

## Notes

This overlay is intentionally small and does not include the full base. A later cumulative bridge rollup will include v35, v35H, v36, v36.1, and v36.2 together so that single-layer download failures do not break the lineage.
