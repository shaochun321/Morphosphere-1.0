# Manifest Count Semantics

`cell_count` is deprecated and ambiguous. It is retained only to avoid breaking earlier code and SQL. New code must use explicit count fields.

## Fields

| Field | Meaning |
|---|---|
| `physical_cell_count` | Count of physical cells in the Stage-1 `PhysicalCellGraphState`. |
| `window_count` | Count of analysis windows. |
| `spacetime_cell_count` | Count of derived diagnostic/runtime carrier rows. Usually `physical_cell_count * window_count`. |
| `cell_count` | Deprecated compatibility field. Do not use in new logic. |
| `extra_json` | JSON payload for count semantics, crosswalk notes, and additive metadata. |

## Source-of-truth boundary

`PhysicalCellGraphState` is the physical source-of-truth. `spacetime_cell` rows are derived from the preneural carrier layer and diagnostic runtime windows.

## Runner policy

Diagnostic runners may keep `execution_mode='diagnostic_full'`, but they must not mark output as `scientific_run`. Count-field repair is not a scientific-run upgrade and does not create V8.6 or V9.
