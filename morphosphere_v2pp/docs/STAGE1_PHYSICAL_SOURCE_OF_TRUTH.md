# Stage-1 Physical Source-of-Truth Boundary

This checkpoint completes the P2 mainline-convergence boundary for the physical
base layer. It does not implement the v8.5.2 execution-fidelity patch and does
not change run outputs to `scientific_run`.

## Canonical names

| Concept | Canonical module/class | Role |
|---|---|---|
| Physical cell aggregate state | `morphosphere.active_exec.stage1_physics.PhysicalCellGraphState` | Mutable physical source-of-truth for mechanics and electrophysiology. |
| Row / JSON / importer state | `CellGraphStateRecord` | Pydantic-compatible interface record derived from physical state. |
| Diagnostic spacetime record | `spacetime_cell` | Runtime/diagnostic row derived from physical/preneneural state over windows. It is not a physical cell. |
| Full causal step | `unified_electromechanical_step` | Mechanics + local strain + MET + membrane + release + afferent. |
| Diagnostic synthetic driver | `DiagnosticDynamicDriver` | Diagnostic-only signal activator. It is not a final biological model. |

## Source-of-truth rule

`PhysicalCellGraphState` is the only mutable physical source-of-truth. Downstream
structures such as `PatchGraph`, `PreNeuralPointSetSlice`, `spacetime_cell`,
`information_fiber`, `transport_current_edge`, `object_hypothesis`, `Xi`, and
confirmation graph records are derived views or diagnostic/runtime records.

## Count semantics

Do not use `cell_count` without qualification. Use these fields in manifests,
reports, and crosswalks:

```text
physical_cell_count  = number of physical cells in PhysicalCellGraphState
window_count         = number of diagnostic/replay windows
spacetime_cell_count = physical_cell_count * window_count
```

The helper `manifest_count_fields()` produces this canonical triplet.

## Driver separation

The physical path is:

```text
PhysicalCellGraphState
  -> compute_all_mechanical_forces
  -> semi_implicit_euler_mechanical
  -> compute_local_strain
  -> MET / hair-cell membrane / calcium-release / afferent dynamics
```

The diagnostic path may still use `DiagnosticDynamicDriver`, but it must be
labeled diagnostic-only and must not be cited as validated cell biology.

## Non-goals in this checkpoint

- No v8.6/v9 changes.
- No `scientific_run` marking.
- No execution-fidelity patch yet.
- No transport/O/Xi/relation-entropy changes yet.
