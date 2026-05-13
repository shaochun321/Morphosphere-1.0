# Morphosphere Online Recursive Sensorium + Full Replay Harness v0.3

## Purpose

`online_recursive_sensorium_full_replay_v0.3` converts the previous batch diagnostic recursion into a clock-ordered online diagnostic loop. The goal is not to add semantics. The goal is to test whether the current chain can process raw events one system-clock step at a time, keep P/R before Xi, and survive replay perturbations without rewriting source facts.

## Main chain

```text
system_clock_entry[n]
  -> raw_event_stream at clock_n
  -> online_preneural_tick_state_v03
  -> online_origin_anchor_tick_v03
  -> online_latent_trajectory_tick_v03
  -> online_o_candidate_tick_v03
  -> online_p_support_tick_v03
  -> online_r_counterstructure_tick_v03
  -> online_xi_boundary_tick_v03
  -> online_feedback_tick_v03
```

## Full replay harness

The full replay harness creates copy-mutated replay buffers and recomputes diagnostic P/R/Xi response. It does not edit `raw_event_stream`, `spacetime_cell`, `information_fiber`, or coordinate snapshots.

Replay scenarios:

```text
baseline
noise_05
noise_10
noise_20
noise_30
hidden_structure_lowfreq
cell_id_permutation
cross_modal_phase_shift
physics_swap_MET_proxy
```

The replay suite directly addresses the historical concerns recorded in `deep.txt`: low/high noise response, hidden structure detection, bottom physics replacement, and the danger of fragile confirmation graphs under over-friendly input.

## P/R and Xi boundary

`P` is predictive/proof support over an online O candidate.

`R` is structured counter-evidence: prediction failure, phase conflict, continuity conflict, or conservation conflict.

`Xi/Xin` is post-P/R unresolved residue. It is not R and cannot directly become P/R.

## Current limitation

This is still diagnostic. It is not `scientific_run`, not final biology, and not a physical proof of a true nervous system. It is a stronger engineering honesty test for the existing chain.
