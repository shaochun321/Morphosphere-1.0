# Mainline Boundary

`morphosphere_v2pp` is the mainline implementation for current Morphosphere work.

## Mainline role

The mainline owns:

- V6/V8/V8.5 diagnostic runtime runners.
- Active execution contracts.
- Stage-1 diagnostic state handling.
- Preneural pointset carrier representation.
- Transport builders and diagnostic transport records.
- Stage-2 object surfaces and P/R candidate machinery.
- SPMS runtime records, confirmation graph, Xi ledger, emergence records, and proxy provenance.
- SQLite schemas, migrations, and diagnostic reports.

## Legacy boundary

`morphosphere_v2` is retained as a legacy V2 reference. It currently contains the clearer early electromechanical physical loop and legacy pre-neural classes such as `PatchAfferentTransmissionGraph` and `PreNeuralSlice`.

Checkpoint 01 does not merge or rewrite those legacy modules. It only establishes the boundary so future checkpoints can migrate or adapterize them without import ambiguity.

## Source-of-truth rule

For current development, the mainline source tree is:

```text
morphosphere_v2pp/src/morphosphere/
```

The top-level legacy tree is not imported by mainline code unless a future explicit adapter is added under `morphosphere.legacy` or `morphosphere.active_exec.*.adapters`.

## P2 update: physical base convergence

Checkpoint P2 adds an explicit Stage-1 physical boundary:

- `PhysicalCellGraphState` aliases the V2-derived dataclass that contains the
  full mutable physical state.
- `CellGraphStateRecord` names the pydantic interface/row model so it is not
  confused with the physical source-of-truth.
- `unified_electromechanical_step` exposes the complete mechanical -> MET ->
  membrane -> release -> afferent causal step in v2pp.
- `manifest_count_fields()` standardizes `physical_cell_count`, `window_count`,
  and `spacetime_cell_count`.

This is a boundary/convergence patch only. The v8.5.2 execution-fidelity patch
remains a later phase.
