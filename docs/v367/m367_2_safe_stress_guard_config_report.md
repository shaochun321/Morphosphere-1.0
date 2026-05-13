# Morphosphere v36.7.2 Safe Stress Guard Config

## Scope

v36.7.2 converts the Pass18 safe stress envelope into a default runtime-configurable guard rule table.
It is a hardening overlay, not an online realtime fuse and not a new theory layer.

## Inputs

- `m366_pass18_safe_stress_envelope.csv`
- `m366_pass18_native_writer_and_safe_envelope.db`
- `m367_1_native_anchor_hardening.db`

## Core Outputs

- `v3672_safe_stress_envelope_rule`: 27 rules
- `v3672_guard_action_table`: 5 actions
- `v3672_guard_regression_result`: 27 rows
- `v3672_guard_lookup_benchmark`: 27 rows

## Guard Action Counts

| action | count |
|---|---:|
| `ALLOW_WITH_AUDIT` | 9 |
| `AUDIT` | 8 |
| `BLOCK_BY_DEFAULT` | 9 |
| `DOWNSCALE` | 1 |

## Regression Gates

| gate | status | observed | required |
|---|---|---:|---:|
| all_pass18_envelopes_loaded | PASS | 27/27 | 27 |
| guard_regression_match | PASS | 27/27 | 27/27 |
| p_core_high_blocked | PASS | 3 | 3 |
| p_boundary_safe_allowed | PASS | 7 | >=7 |
| outside_high_blocked | PASS | 3 | 3 |
| coordinate_invariance_ci_inherited | PASS | PASS | PASS |
| legacy_db_mutation_absent | PASS | 0 | 0 |

## Boundary

- This is a rule-table hardening layer over Pass18 evidence.
- It does not mutate legacy DBs.
- It does not implement online Polyphonic Guard or realtime fuse.
- It inherits coordinate invariance CI from v36.7.1.

## DB Integrity

`ok`
