# Morphosphere Execution Paths (V8)

According to the Morphosphere Total Rules V8, the execution pipeline is strictly divided into three layers to separate core ontology creation from non-blocking analysis and accounting.

## 1. Hot Path (Synchronous)
These operations happen in the main execution loop. They block the pipeline because the next frame depends entirely on their output.
- `SystemClock` advancement
- Data shape / schema validation
- `PreNeuralPointSetSlice` extraction
- **Transport Operator** (Hard gating, distance matrix, Sparse Bidirectional NN)
- **PR Decomposition** (Graph Laplacian smoothing, sparse residual iterative solver)
- `P_Band` and `R_Band` object freezing

## 2. Warm Path (Delayed Synchronous)
These operations occur after the primary objects are frozen but before the system advances to the next major phase.
- Baseline consistency checks (`coherence`, `transport_consistency`)
- Candidate invariants checks
- Baseline anomaly flagging

## 3. Cold Path (Asynchronous)
These operations perform deep analysis and accounting without blocking the primary physics execution.
- **External Ledgers**: `PhysicalLedger`, `InformationLedger`, `ExternalEntropyLedger` updates and `ExternalIsolationReport` generation.
- **Transform Auditing**: Recording all `domain -> codomain` structural changes.
- **External Transitional Pilots**: 
  - `transport_pilot_ot_cpd` runs OT/Sinkhorn and generates candidate reports.
  - `pr_decomposition_pilot_glsr` generates parallel experimental decomposition candidates.
  - `noether_entropy_ledger_pilot` generates higher-order variational reports.

*Note: The distinction in execution paths is purely for computational routing; it does not indicate that ledger or audit quantities are somehow less "true" than the physical point-sets.*
