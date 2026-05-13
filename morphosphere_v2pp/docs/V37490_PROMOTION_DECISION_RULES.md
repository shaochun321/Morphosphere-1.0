# Promotion Decision Rules — v37.4.90

## Blueprint Reference: §12, §21

## Decision Matrix

### PROMOTE (§12.1)
Conditions (ALL must be satisfied):
```
B wins ≥ 2/3 stress dimensions
B wins ALL 3 of: survival, adaptation, compute
compute_overhead_pct ≤ 20%
holdout_drift < 2σ tolerance
singularity_count = 0 OR well-managed
collapse_count = 0
```

### KEEP_AS_CANDIDATE (§12.2)
Conditions:
```
B wins ≥ 1/3 but not all 3
OR tie on any dimension
OR B overhead borderline (15-20%)
```
Action: Retain A as default, keep B for further testing.

### REJECT (§12.3)
Conditions (ANY triggers rejection):
```
B overhead > 20% with no clear benefit
B singularity causes data loss
B false attractor lock-in rate > A
B fails holdout evaluation
```

## Tie-Breaker Rule
When scores are tied: **Always prefer A** (Occam's razor).

## Current Decision: KEEP_AS_CANDIDATE
- Score: A=1, B=2 (B wins survival + adaptation, loses compute dimension)
- B wins 2/3 but not all 3 → Occam's razor keeps A
- Rationale: B shows promise but hasn't achieved clean sweep required for promotion

## Degradation Strategy (§21)
1. If B fails → Keep A, freeze B as rejected candidate
2. If B partial success → Keep A default, retain B as candidate (CURRENT STATE)
3. If B succeeds but overhead too high → Keep A, explore C as compromise
