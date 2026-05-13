# V37.4.90 A/B Stress Benchmark Protocol

## Blueprint Reference
MORPHOSPHERE.2026.5.10.1

## Objective
Validate whether topological inertia (Engine B) genuinely outperforms manual strata
(Engine A) under controlled stress conditions, as specified in §10.

## Three Engines

| Engine | Strategy | Key Parameters |
|--------|----------|----------------|
| A — Manual Strata | Fast/slow/prior 3-layer Oja learning | alpha_fast=0.18, alpha_slow=0.05 |
| B — Topological Inertia | M_eff-gated Hebbian with 7-input mass | M_max=8.0, eta=0.18, κ=0.15 |
| C — Guarded Hybrid | A's structure + B's alpha modulation | alpha_mod=[0.5, 1.5] |

## Six Data Streams (§10.3)

1. **Public replay stream** — CTC seq01 calibration data (real)
2. **Chaos Xin storm** — 30 ticks of random noise injection
3. **Novelty shift stream** — 20 ticks of sudden pattern change
4. **Contradiction stream** — 15+15 ticks of false attractor build/attack
5. **Staleness stream** — 50 ticks of no input (decay-only)
6. **Compute stress stream** — 5 rounds of 20→100 cells scaling

## Verification Checks (38 total)
See `test_outputs/ab_test_report.json` for full results.

## Promotion Decision Rules (§12)
- **PROMOTE**: B must win ALL 3 dimensions (survival, adaptation, compute)
- **KEEP_AS_CANDIDATE**: B wins partially, tie → prefer A
- **REJECT**: B shows singularity, collapse, or ≥20% overhead

## Data Discipline (§14)
- Calibration data: CTC seq01 (adjustable)
- Frozen holdout: CTC seq02 (never adjustable)
- No holdout re-tuning after evaluation
