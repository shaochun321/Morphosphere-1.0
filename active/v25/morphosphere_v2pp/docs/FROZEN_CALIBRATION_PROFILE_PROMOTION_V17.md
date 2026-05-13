# Frozen Calibration Profile Promotion Gate v1.7

v1.7 turns calibration recommendations into a staged frozen profile candidate, but does not apply it. External Lab and sensor-memory recommendations may propose a profile; they cannot hot-swap the runtime or rewrite source facts.

## Promotion rule

A candidate can only be promoted by creating a new frozen calibration profile and running a fresh pipeline. Existing DB facts remain immutable.

## Required gates

1. Full replay battery passes.
2. Real external physical data gate passes.
3. P/R-Xi boundary audit passes.
4. Source fact digests pass.
5. Human approval is recorded.
6. Rollback plan is present.

## Current status

Staged, not promoted. Blocked by pending real external data and pending human approval.
