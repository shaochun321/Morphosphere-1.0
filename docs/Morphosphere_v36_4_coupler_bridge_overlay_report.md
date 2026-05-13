# Morphosphere v36.4 Constrained Variational Coupler Bridge Overlay

## Artifact identity

- `artifact_type = ENGINEERED_BRIDGE_OVERLAY`
- `includes_full_base = false`
- `not_a_full_lineage = true`

This package is a single-layer bridge overlay. It does not include the full v25-v34 base, v35, v35H, v36, v36.1, v36.2, v36.3, or v36.5. It is meant to be applied onto an existing Morphosphere tree and later merged into a cumulative bridge rollup / full-lineage rebase.

## Purpose

v36.4 turns the v36.3 role definitions into a constrained discrete variational coupler. The coupler does not claim to find a true global continuous spacetime trajectory. It builds bounded R-band candidates under a dissipation light cone, P-island tunnel, ledger-decayed beam search, Xin triage, and pseudo-continuity audit.

## Implemented tables

- `v364_p_anchor_tunnel_profile`
- `v364_dissipation_light_cone`
- `v364_r_band_candidate_search`
- `v364_dynamic_beam_state`
- `v364_variational_coupling_cost`
- `v364_xin_triage_policy`
- `v364_pseudo_continuity_score`
- `v364_cognitive_field_residual_audit`
- `v364_coupler_decision_report`
- `v364_downgrade_contract`
- `v364_acceptance_report`

## Core formula

```text
C_total(B_R) =
  lambda_R      * C_R_continuity(B_R)
+ lambda_P      * C_P_anchor(B_R)
+ lambda_X      * C_Xin_residual(B_R)
+ lambda_mu     * C_metric_distortion(B_R)
+ lambda_L      * C_ledger_violation(B_R)
+ lambda_smooth * C_pseudo_smoothing(B_R)
```

Search is bounded by:

```text
B_R in Beam_K(candidate_blocks constrained by:
  dissipation_light_cone,
  P_island_tunnel,
  ledger_budget,
  kernel_bandwidth_limit,
  max_scale_switch,
  Xin_recursion_budget)
```

## Downgrade / suspension / rejection notes

| Original philosophical-mathematical construct | Downgraded object | Correction mechanism | Rejected interpretation |
|---|---|---|---|
| R seeks a true continuous spacetime band | `r_band_candidate` | Dissipation light cone + P tunnel + ledger-decayed beam search | Not a true continuous trajectory |
| P as inertial reference | `p_stasis_anchor_proxy` | Anchor drift and persistence adjust tunnel weights | Not absolute rest |
| Xin as noncontinuizable residue | `xin_triage_policy` | Foreground/background/deferred/thermalized/external leakage classes | Not waiting P |
| Cognitive field equation | `cognitive_field_residual_audit` | Audit only, never optimizer loss | Not physical field equation |
| Least action over all paths | `top_k_local_path_scoring` | Bounded beam and local neighborhoods | Not global optimum |

## Guardrails

- `source_facts_rewritten = 0`
- `hot_swap_allowed = 0`
- `semantic_label_in_mainline = 0`
- `global_optimum_claimed = 0`
- `physical_field_equation_claimed = 0`
- `field_residual_used_as_loss = 0`
- `Xin direct to P/R = 0`

## Local commands

```bash
tar --zstd -xf Morphosphere_v36_4_coupler_bridge_overlay.tar.zst
cd Morphosphere_v36_4_coupler_bridge_overlay
./RUN_EXAMPLES.sh
python3 active/v364/scripts/check_v364.py --db outputs/m364.db
python3 active/v364/scripts/query_v364.py --db outputs/m364.db --mode decisions --limit 5
python3 active/v364/scripts/audit_v364_coupler.py --db outputs/m364.db
```

## Result summary

- `v364_p_anchor_tunnel_profile`: 60
- `v364_dissipation_light_cone`: 240
- `v364_r_band_candidate_search`: 120
- `v364_dynamic_beam_state`: 600
- `v364_variational_coupling_cost`: 120
- `v364_xin_triage_policy`: 85
- `v364_pseudo_continuity_score`: 120
- `v364_cognitive_field_residual_audit`: 40
- `v364_coupler_decision_report`: 40
- `v364_acceptance_report`: 12 / 12 PASS
