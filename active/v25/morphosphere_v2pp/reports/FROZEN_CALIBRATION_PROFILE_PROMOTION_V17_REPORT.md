# Frozen Calibration Profile Promotion Gate v1.7

## Decision

`STAGED_FROZEN_PROFILE_NOT_PROMOTED_PENDING_REAL_EXTERNAL_DATA_AND_HUMAN_APPROVAL`

The v06 fitted candidate and v16 sensor-fusion calibration recommendations were bundled into a staged frozen profile candidate, but the profile was not promoted or applied.

## Main blockers

- Real external physical data gate is not cleared.
- Human approval has not been granted.

## Protected boundaries

- No hot-swap.
- No source-fact rewrite.
- P/R remains before Xi.
- SQLite remains ledger-only.
- Any approved profile must be a new frozen calibration profile run, not a live mutation.

## Artifacts

- `morphosphere_v2pp/configs/frozen_calibration_profile_v17_candidate.json`
- `runtime_store/v17/manual_approval_packet_v17.json`
- `runtime_store/v17/promotion_decision_v17.json`
- `runtime_store/v17/rollback_plan_v17.json`
