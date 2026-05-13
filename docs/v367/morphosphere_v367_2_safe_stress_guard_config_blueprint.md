# Morphosphere v36.7.2 Blueprint: Safe Stress Envelope Runtime Config

## Version

`v36_7_2_safe_stress_envelope_runtime_config`

## Goal

Turn the Pass18 safe stress envelope into a default guard rule table that can be loaded by deployment checks and future runtime components.

## Non-goals

- No online realtime fuse.
- No new theory object.
- No destructive migration of legacy DBs.
- No replacement of P/R/Xin logic.

## Core Tables

```text
v3672_safe_stress_envelope_rule
v3672_guard_action_table
v3672_guard_regression_result
v3672_guard_lookup_benchmark
v3672_regression_gate
```

## Guard Actions

```text
ALLOW
ALLOW_WITH_AUDIT
AUDIT
DOWNSCALE
BLOCK_BY_DEFAULT
```

## Policy

- P-core high intensity or collapse-prone combinations: `BLOCK_BY_DEFAULT`.
- P-core partial collapse: `DOWNSCALE`.
- P-boundary safe envelopes: `ALLOW_WITH_AUDIT`.
- Outside-support high/failure: `BLOCK_BY_DEFAULT`.
- Outside-support low/medium: `AUDIT`.

## Acceptance

- All 27 Pass18 envelope cells loaded.
- All scenarios resolve to a configured guard action.
- Coordinate invariance CI remains PASS.
- No legacy DB mutation.
