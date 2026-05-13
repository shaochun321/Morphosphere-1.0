# P3 Pre-Neural Carrier Boundary

## Status

`morphosphere_v2pp` is the mainline implementation.  `morphosphere_v2` remains a legacy/reference implementation.  The pre-neural carrier layer is now described by an explicit boundary so the legacy and v8/v8.5 representations cannot be silently conflated.

## Canonical boundary

The canonical boundary is:

```text
PhysicalCellGraphState
  -> PatchAfferentTransmissionGraph
  -> PreNeuralCarrierSlice
  -> PreNeuralPointSetSlice / transport / stage2 runtime views
```

`PreNeuralCarrierSlice` is an implementation-neutral crosswalk.  It can be created from the current v8/v8.5 `PreNeuralPointSetSlice`, or from a legacy v2 `PreNeuralSlice`-like object via a duck-typed adapter.

## Patch graph distinction

### Full mainline graph

`PatchAfferentTransmissionGraph` is the full preneural runtime graph.  It contains typed nodes and typed edges, spatial anchors, source cell IDs, patch weights, and continuous signal state.

### Minimal diagnostic graph

`stage1_physics.PatchGraph` remains a minimal diagnostic aggregation view used by current v8/v8.5 diagnostic runners.  It is useful but it is not the full patch-afferent graph.

Use `build_patch_afferent_graph_from_minimal_patch_graph()` when a diagnostic runner starts from the minimal `PatchGraph` but downstream code requires the full boundary semantics.

## Slice distinction

### Current v8/v8.5 implementation

`PreNeuralPointSetSlice` is the current v8/v8.5 implementation.  It carries geometry nodes, signal windows, topology, signal-window references, and provenance.

### Legacy v2 implementation

`PreNeuralSlice` is the legacy v2 implementation.  It remains a valid reference implementation but must not be imported as the mainline package in the same environment as v2pp, because both projects use the same Python package name `morphosphere`.

Use the adapter functions in `active_exec.preneural.adapters` to convert legacy-like slices into the carrier boundary.

## Source-of-truth rules

1. `PhysicalCellGraphState` is the physical source-of-truth.
2. `PatchAfferentTransmissionGraph` is the full preneural carrier graph boundary.
3. `PatchGraph` is a minimal diagnostic aggregation view, not the full graph.
4. `PreNeuralCarrierSlice` is the common slice crosswalk.
5. `PreNeuralPointSetSlice` is the current v8/v8.5 slice implementation.
6. `spacetime_cell` and `information_fiber` remain diagnostic/runtime derived records, not physical source-of-truth objects.

## Deployment note

Do not install `morphosphere_v2` and `morphosphere_v2pp` into the same virtual environment.  Install the mainline project from `morphosphere_v2pp` only.  Keep `morphosphere_v2` for source review or legacy comparison.
