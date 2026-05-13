# Morphosphere v36.6 Pass13 — Native Replay Skeleton + Upper-Layer Stress Evidence

Replay samples: **70**; scenarios: **7**; stage outputs: **5880**; case studies: **20**.

## Transition summary

| scenario | transition counts |
|---|---|
| `baseline` | {'stable_retained': 70} |
| `coordinate_jitter` | {'observe_retain_shift': 7, 'stable_retained': 63} |
| `support_dropout` | {'observe_retain_shift': 13, 'stable_retained': 56, 'P_or_stable_to_R_focus': 1} |
| `counter_boost` | {'P_or_stable_to_R_focus': 66, 'stable_retained': 4} |
| `xin_spike` | {'R_or_P_to_Xin_escalation': 69, 'stable_retained': 1} |
| `masking_failure` | {'observe_retain_shift': 13, 'stable_retained': 33, 'P_or_stable_to_R_focus': 24} |
| `semantic_attack` | {'semantic_backwrite_blocked': 70} |

## Information-change chain

```text
source / envelope
-> information 3D/4D backprojection
-> trajectory support / T
-> O candidate
-> P/R/Xin role split
-> counter-evidence / masking
-> external entropy ledger
-> attention path
-> hyperedge incidence
-> variational action / Xin_var
-> Xin carrier / external readout
-> process_window query surface
```

## Boundaries

This is native-shaped replay over materialized data, not a native synchronous online runtime. Perturbations are deterministic projections and do not rewrite source facts.

## Evidence claims

| claim | support | limitation |
|---|---|---|
| The project can replay information points into T/O/P/R/Xin roles for selected samples. | pass13_toprxin_replay_output rows=490 | native-shaped over materialized data, not online runtime |
| Counter-evidence boost produces R-focused transitions. | pass13_state_transition_summary rows=66 | deterministic projection, not source rerun |
| Xin spike produces Xin escalation. | pass13_state_transition_summary rows=69 | requires future empirical perturbation input |
| Semantic backwrite is blocked. | pass13_state_transition_summary rows=70 | tests boundary behavior, not semantic competence |
| External readout remains read-only in replay outputs. | pass13_hyper_variational_readout_output rows=490 | minimal readout module only |
