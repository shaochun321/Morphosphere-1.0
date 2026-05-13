# V8.5 Diagnostic to Mainline Crosswalk

This document is part of the mainline convergence checkpoint. It prevents V8.5 diagnostic SPMS rows from silently replacing source-of-truth mainline objects.

## Non-negotiable interpretation rules

- `PhysicalCellGraphState` is the physical-cell source of truth.
- `spacetime_cell` is a derived diagnostic/runtime carrier row, not a physical cell.
- `information_fiber` is a derived signal-window row, not raw electrophysiology or final biological event evidence.
- `transport_current_edge` is a diagnostic transport-current record, not automatically a fully trusted `transport_operator`.
- `object_hypothesis` is a P/R/O candidate view, not a certified object, frozen P band, or scientific conclusion.
- Empty legacy tables such as `t_surface`, `p_band_record`, or `r_band_record` may be intentionally empty in SPMS-layer diagnostic runs. The crosswalk must be checked before treating emptiness as failure.

## Manifest count semantics

Use explicit fields:

```text
physical_cell_count  = number of Stage-1 physical cells
window_count         = number of analysis windows
spacetime_cell_count = number of derived diagnostic runtime rows
cell_count           = deprecated compatibility count
```

For a diagnostic run with 50 physical cells and 10 windows:

```text
physical_cell_count  = 50
window_count         = 10
spacetime_cell_count = 500
```

Do not interpret `spacetime_cell_count` as the number of physical cells.

## Crosswalk storage

The canonical source is implemented in:

```text
src/morphosphere/mainline/crosswalk.py
```

The database materialization is created by:

```text
migrations/011_mainline_manifest_crosswalk.sql
```

Key rows include:

| Diagnostic table | Mainline concept | Role | Forbidden use |
|---|---|---|---|
| `spacetime_cell` | preneural geometry / pointset view | derived | Do not treat as physical cell source-of-truth. |
| `information_fiber` | preneural signal window view | derived | Do not treat as raw electrophysiology or final biology. |
| `transport_current_edge` | diagnostic transport process view | derived | Do not claim transport realism while weights/gating/costs remain trivial. |
| `object_hypothesis` | P/R candidate view | derived | Do not treat as certified/frozen object. |
| `t_surface` | legacy/mainline T surface | derived or intentionally empty | Do not fail an SPMS-only diagnostic run solely because it is empty. |
| `p_band_record` | legacy/mainline primary band | derived or intentionally empty | Do not treat empty rows as failed diagnostic object formation. |
| `relation_entropy_record` | diagnostic ledger | report-only | Do not use for refutation while entropy remains synthetic. |

## Acceptance checks

```sql
SELECT physical_cell_count, window_count, spacetime_cell_count, cell_count
FROM run_manifest;

SELECT diagnostic_table, semantic_role, source_of_truth, forbidden_use
FROM v85_to_mainline_crosswalk
ORDER BY diagnostic_table;
```

Expected: `physical_cell_count`, `window_count`, and `spacetime_cell_count` are distinguishable; `v85_to_mainline_crosswalk` contains entries for SPMS, legacy/mainline, proxy, entropy, and emergence tables.
