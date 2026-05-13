# Morphosphere v36.6 Pass20: Native Writer Expansion + RMI Query Benchmark

## Position
Pass20 expands the v37-readiness native writer prototype and benchmarks relational measure index (RMI) hash variants. It does **not** claim online native runtime and does **not** mutate legacy DBs.

## Core Results

| Item | Value |
|---|---:|
| Expanded writer-emitted facts | 855 |
| FK validation pass | 848/855 |
| H1 false-neighbor collision groups | 3 |
| H3 false-neighbor collision groups | 0 |
| H3 average bucket candidates | 1.0000 |
| Coordinate invariance CI | PASS |
| DB integrity | ok |

## RMI Benchmark

| Variant | Meaning | Avg bucket | Max bucket | Collision groups | False-neighbor groups | Verdict |
|---|---|---:|---:|---:|---:|---|
| H1 | measure-only coarse | 1.0070 | 2 | 3 | 3 | RISKY |
| H2 | measure + trajectory | 1.0000 | 1 | 0 | 0 | PREFERRED |
| H3 | measure + dark-grid + information point | 1.0000 | 1 | 0 | 0 | PREFERRED |

## Interpretation

- H1 is intentionally risky and is retained only as a warning baseline.
- H3 is the preferred v37-readiness hash because it mixes measure information with dark-grid and bottom evidence anchors.
- Expanded writer facts are L3-shaped emitted facts over materialized targets; they are stronger than post-hoc inference but still not a destructive migration of legacy raw FK.

## Acceptance

- **PASS**: expanded writer facts cover all L2 safe candidates — observed `855`, requirement `expected 855`
- **WARN**: FK validation targets hit materialized tables — observed `848/855`, requirement `all expanded facts should hit info/traj/evidence/process/ledger/anchor targets`
- **PASS**: H1 exposes collision risk — observed `3`, requirement `measure-only hash should be audited and not preferred`
- **PASS**: H3 removes false-neighbor collisions in sample — observed `0`, requirement `dark-grid anchored hash should avoid false-neighbor groups`
- **PASS**: H3 query bucket size is near O(1) — observed `1.0000`, requirement `average candidate bucket <= 1.05`
- **PASS**: coordinate invariance CI default gate passes — observed `PASS`, requirement `rigid translation must preserve roles`
- **PASS**: legacy DBs are not mutated — observed `0`, requirement `must remain 0`
