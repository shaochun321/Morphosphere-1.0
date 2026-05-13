# Morphosphere v36 Metric Bridge Overlay Report

Generated: 2026-05-05T10:04:53.055672+00:00

## Identity

This package is `v36_metric_bridge_overlay`.

It is an `ENGINEERED_BRIDGE_OVERLAY`, not a full lineage package. It does not include the v25-v34 full base, v35, v35H, or v36.1-v36.5 contents. It can be applied on top of an existing Morphosphere tree.

## Implemented scope

v36 implements a cautious bridge for the ideas from the dissipative metric and Xin curvature blueprint:

- stable dissipative source registry
- finite-window Delta Xin fallback / diagnostic rows
- provisional information-energy metric proxy
- raw coordinate anchor audit
- Ricci-like curvature proxy without Ricci claim
- singularity candidate audit rows
- topological heat bath accounting
- downgrade/minimization/forbidden-interpretation contract
- v36 guardrail and acceptance reports

## Counts

```text
v36_dissipative_source_registry       80
v36_delta_xin_field                   64
v36_information_energy_metric_proxy  160
v36_metric_anchor_audit              160
v36_curvature_proxy                  120
v36_singularity_candidate             21
v36_topological_heat_bath             17
v36_downgrade_contract                 7
v36_acceptance_report              12 / 12 PASS
```

## Guardrail status

```text
source_facts_rewritten = 0
hot_swap_allowed = 0
semantic_label_in_mainline = 0
physical_metric_claimed = 0
delta_xin_as_main_definition = 0
ricci_claimed = 0
raw_coordinate_replaced = 0
```

## Downgrade / minimization / correction contract

| Original philosophical-mathematical construct | Why it is not directly adopted | Engineering object | Minimized / corrected as | Forbidden interpretation |
|---|---|---|---|---|
| Continuous information-energy metric | No continuous physical metric base | `v36_information_energy_metric_proxy` | Local ledger-scored proxy only | Not physical spacetime metric |
| Differential Xin field | No observable continuous Xin field | `v36_delta_xin_field` | Fallback diagnostic finite-window delta | Not a true differential field |
| Ricci curvature | No smooth manifold or PDE base | `v36_curvature_proxy` | Weighted local curvature-like audit | Not Ricci curvature |
| Singularity | Would overstate physical/geometric claim | `v36_singularity_candidate` | SNR and ledger-gated audit candidate | Not physical singularity |
| Topological surgery | Deletion violates ledger conservation | `v36_topological_heat_bath` | Reversible digest and ledger transfer | Not true topology surgery |
| Coordinate replacement | Raw coordinates remain verification anchors | `v36_metric_anchor_audit` | Anchor drift audit forbids replacement | Coordinates are not removed |
| Semantic motion/rest | Semantic labels forbidden in mainline | external readout only | Readout blocked from backwrite | Not semantic truth |

## Suspended

- v36.1 external ledger variational action is not implemented in this package.
- v36.2 variational action revision is not implemented in this package.
- v36.3 R spacetime band / Xin noncontinuity is not implemented here.
- v36.4 constrained variational coupler is not implemented here.
- Full lineage rebase remains pending.

## Rejected

- claiming `mu_IE` as real spacetime metric
- using Delta Xin as the main definition of Xin
- claiming Ricci curvature or PDE implementation
- replacing raw coordinate anchors
- semantic labels in mainline tables
- direct source fact rewriting

## Local commands

```bash
tar --zstd -xf Morphosphere_v36_metric_bridge_overlay.tar.zst
cd Morphosphere_v36_metric_bridge_overlay
./RUN_EXAMPLES.sh
python3 active/v36/scripts/check_v36.py --db outputs/m36.db
python3 active/v36/scripts/query_v36.py --db outputs/m36.db --limit 5
python3 active/v36/scripts/audit_v36_downgrade.py --db outputs/m36.db
```
