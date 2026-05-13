# Morphosphere Online Recursive Sensorium + Full Replay Harness v0.3

This diagnostic layer converts dynamic_recursive_v0.2 and pr_restoration_v0.2.2 into a clock-ordered online sensorium.

## Core boundaries

- system_clock_entry is the explicit time source.
- Source facts are read-only; replays use copy-mutated replay buffers.
- P/R remains the canonical decomposition layer; Xi is post-P/R unresolved residue.
- No semantic labels participate in raw_event -> trajectory -> O/P/R/Xi formation.

## Counts

- online_clock_tick_v03: 10
- online_preneural_tick_state_v03: 500
- online_latent_trajectory_tick_v03: 50
- online_p_support_tick_v03: 50
- online_r_counterstructure_tick_v03: 15
- online_xi_boundary_tick_v03: 50
- full_replay_scenario_v03: 9
- full_replay_event_buffer_v03: 13500
- full_replay_result_v03: 9

## Full replay results

- baseline: PASS; P=0.9556; R=0.0000; Xi=0.1602; baseline online replay remains stable
- cell_id_permutation: PASS; P=0.9556; R=0.0000; Xi=0.1602; trajectory response invariant to identifier permutation
- cross_modal_phase_shift: PASS; P=0.2281; R=0.3333; Xi=0.7886; cross-modal phase lag produces detectable R/Xi pressure
- hidden_structure_lowfreq: PASS; P=0.5236; R=0.0350; Xi=0.4723; hidden structure detected as new_P_candidate
- noise_05: PASS; P=0.9324; R=0.0000; Xi=0.1770; low-noise replay preserves P/R without collapse
- noise_10: PASS; P=0.9100; R=0.0000; Xi=0.1932; low-noise replay preserves P/R without collapse
- noise_20: PASS; P=0.8599; R=0.0000; Xi=0.2295; high-noise replay raises Xi/R pressure without crashing
- noise_30: PASS; P=0.8093; R=0.0085; Xi=0.2660; high-noise replay raises Xi/R pressure without crashing
- physics_swap_MET_proxy: PASS; P=0.1202; R=0.9721; Xi=0.8084; MET proxy produces nonuniform signal; downstream P/R/Xi replay runs without source rewrite
