# Morphosphere v36.6 Pass16: Source-Level Rerun Harness + CTC02 Upper Overlay + Measure Anchor Hash

This pass continues Pass15 by moving selected stress checks closer to source-level rerun. It still does not claim online native runtime.

## Counts

- pass16_source_rerun_case: 120
- pass16_source_level_rerun_result: 960
- pass16_ctc02_overlay_projection: 532
- pass16_measure_anchor_hash_registry: 855

## Source-level rerun summary

| scenario | rows | role changed | P→R | →Xin | stable | max |delta path| | mean ΔP | mean ΔR | mean ΔXin | collapse | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 120 | 0 | 0 | 0 | 120 | 0 | 0 | 0 | 0 | 0 | INFO |
| rigid_translation | 120 | 0 | 0 | 0 | 120 | 2.032e-15 | 0 | 0 | 0 | 0 | PASS |
| source_counter_edge_injection | 480 | 418 | 394 | 20 | 62 | 6.822 | -0.1999 | 0.3345 | 0.1147 | 60 | WARN |
| support_dropout_source | 120 | 87 | 67 | 19 | 33 | 0.6112 | -0.08675 | 0.1301 | 0.09205 | 1 | WARN |
| xin_discontinuity_source_spike | 120 | 86 | 6 | 80 | 34 | 3.11 | -0.2494 | 0.3631 | 0.3562 | 15 | WARN |

## CTC01/02 overlay comparison

| seq | windows | mean P | mean R | mean Xin | mean attention | effective share | novelty share | mean arity | mean action | mean Xin_var | R-band share | carrier share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01 | 241 | 0.5699 | 0.3012 | 0.2885 | 0.3910 | 0.191 | 0.191 | 7.734 | 0.5254 | 0.3433 | 0.842 | 1.000 |
| 02 | 291 | 0.5501 | 0.2978 | 0.2714 | 0.3806 | 0.072 | 0.072 | 7.581 | 0.5238 | 0.3346 | 0.753 | 1.000 |

## Backprojection directness / anchor hash

| tier | count | share | interpretation |
|---|---:|---:|---|
| L1_measure_anchor_hash_materialized | 855 | 1.000 | existing refs hit materialized v25 objects, but raw direct_fk flag remains false |

## Acceptance

- A1: PASS (PASS) — rigid translation source-level rerun should preserve roles
- A2: WARN ((394, 60)) — counter source injection should trigger R without P core collapse
- A3: WARN ((80, 15)) — source discontinuity should route some samples to Xin without global collapse
- A4: PASS (291) — CTC02 overlay projection present without retuning
- A5: PASS (855) — measure anchor hash available for hypernode backprojection
- A6: WARN (0) — native raw direct FK remains future target

## Boundaries

- Source-level rerun here recomputes trajectory geometry from perturbed source information points for selected samples. It is stronger than field-only projection, but still not an online native runtime.
- CTC02 upper overlay is same-formula/no-retune proxy projection; it is not a full v35-v36.6 generated overlay tree.
- Measure anchor hash improves hard anchoring, but raw direct FK remains 0 until upstream writers emit direct refs natively.