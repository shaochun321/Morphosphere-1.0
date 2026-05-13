# Sensor Fusion Memory and Drift Calibration v1.6

v1.6 converts v1.5 frame-by-frame multi-rate synchronization into cross-window memory.

## Purpose

- Estimate long-term lag and drift per clock domain.
- Estimate phase bias per modality pair.
- Track binding confidence and Xi pressure over windows.
- Stage calibration recommendations without applying them.

## Main tables

- `clock_domain_memory_state_v16`
- `phase_bias_memory_state_v16`
- `fusion_confidence_memory_trace_v16`
- `domain_calibration_recommendation_v16`
- `drift_memory_replay_result_v16`

## Governance

SQLite remains a ledger. Calibration recommendations are staged only. Human review is required before any frozen profile promotion. P/R remains before Xi.
