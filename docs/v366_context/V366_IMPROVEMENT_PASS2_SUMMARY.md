# v36.6 Improvement Pass 2 Summary

Pass2 is an additive engineering pass over the v36.6 process-window materialization. It does not rewrite source facts and does not promote proxy bridges to truth.

## New DBs

- `outputs/v366/m366_improvement_pass2.db`
- `outputs/v366/m366_process_window_pass2.db`

## New capabilities

1. Stage-2 object-surface bridge rows: 532
2. R-chain to concrete mask template bindings: 532
3. Preneural process-window supplements: 500
4. Preneural process-window members: 2000
5. Hypernode FK upgrades applied after normalization: 390 / 855
6. Process windows upgraded by pass2: 163
7. Weak process windows remaining: 330

## Boundary

- `direct_stage2_fk_available = 0` for Stage-2 proxy bridges.
- `direct_r_to_mask_fk = 0` for R-chain mask template bindings.
- Hypernode `direct_fk_available_after = 1` only where the target row exists.
- `semantic_writeback_allowed = 0`.
- `source_facts_rewritten = 0`.
