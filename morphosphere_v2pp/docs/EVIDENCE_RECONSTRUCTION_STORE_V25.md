# Evidence Reconstruction Store v2.5

v2.5 reconstructs the evidence layer from the v2.4 CTC source-verified baseline. It preserves source facts and appends traceable tables and runtime sidecars:

```text
information_point_v25
  -> coordinate_transform_trace_v25
  -> trajectory_window_trace_v25
  -> p_spacetime_measure_v25 / r_counter_measure_v25 / xi_residual_surface_v25
  -> decision_evidence_bundle_v25
```

Core invariants:

- Source facts are not rewritten.
- P/R before Xi is preserved.
- Xi reentry policy is via_o_candidate_only.
- External entropy ledger references are carried into every evidence bundle.
- SQLite is an audit ledger/index; runtime_store/v25 contains payloads.
