# Frozen Profile Replay Sandbox v1.8

Decision: `SANDBOX_COMPLETED_CANDIDATE_REMAINS_STAGED_NOT_PROMOTED`

This package compares the baseline governed profile with the v1.7 frozen candidate profile in an isolated sandbox. The candidate is not applied, not promoted, and not hot-swapped.

## Counts

- Scenarios: 10
- Candidate-winning sandbox scenarios: 8
- Auto-applied: False
- Candidate promoted: False
- Manual review required: True

## Blockers

- real_external_data_gate
- human_approval_gate
- candidate_not_replayed_against_true_external_physical_runtime

## Boundary

P/R remains before Xi. Source facts are not rewritten. Severe anomalies must remain visible as R/Xi pressure.
