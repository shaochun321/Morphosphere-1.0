# Morphosphere P/R Restoration + Xi Boundary Repair v0.2.2

## Purpose

This patch repairs a boundary problem that appeared after the state-separation and
dynamic-recursive layers became dominant: `Xin/Xi` must not replace `P/R`.

The correct chain restored by this patch is:

```text
raw_event_stream
  -> origin_anchor
  -> latent_trajectory / T-trace
  -> O_candidate_bridge
  -> P/R decomposition
  -> Xi boundary guard
```

## Corrected definitions

- `T`: Trace / Trajectory Evidence. A nonsemantic time-ordered trace extracted
  from raw events under origin-relative constraints.
- `O`: Organized Candidate. A candidate support surface or trajectory bundle,
  not a named semantic object.
- `P`: Predictive / Proof Support. Positive support for an O candidate under
  prediction, continuity, conservation, phase and memory tests.
- `R`: Refutational Counter-Structure. Structured counter-evidence against an
  O candidate. R is **not residual**.
- `Xi/Xin`: Unresolved Residue Carrier. Protected residue that is neither
  explained by P nor structured as R. Xi may re-enter only through
  O_candidate_bridge, never directly as P or R.

## Historical issues handled

`historical_issue_register_v022` records nine issues:

1. P/R was at risk of being shadowed by Xi/Xin.
2. R was too close to residual terminology.
3. Layer interfaces were implicit rather than machine-readable.
4. External ledger tables existed but were empty.
5. Legacy hand-tuned P/R scoring needed isolation.
6. Matrix/Foam substrate remains absent.
7. Online recursion is not yet implemented.
8. Full raw perturbation replay remains incomplete.
9. Real physical data driver is not active.

The patch resolves or mitigates the first five and keeps the last four open
instead of pretending they are solved.

## New database tables

```text
historical_issue_register_v022
layer_interface_contract_v022
layer_port_contract_v022
pr_term_registry_v022
o_candidate_bridge_v022
p_predictive_support_v022
r_counterstructure_v022
xi_boundary_guard_v022
pr_decomposition_binding_v022
external_ledger_status_v022
pr_restoration_run_manifest_v022
pr_restoration_acceptance_report_v022
```

## Source-fact boundary

The patch is append-only. It does not rewrite:

```text
spacetime_cell
information_fiber
raw_event_stream
cell_spatial_coordinate_snapshot
information_relative_coordinate_snapshot
preneural_node_state
dynamic_origin_anchor_state
dynamic_latent_trajectory_state
xin_residue_dynamics
system_clock_entry
```

The manifest stores before/after row counts for these tables.

## External ledger status

The package already had external ledger schemas, but the dynamic v0.2 database
had no active rows in them. This patch diagnostically populates:

```text
external_entropy_ledger
external_conserved_quantity_ledger
external_dissipation_ledger
external_noise_budget_ledger
external_anomaly_ledger
external_isolation_report
```

These ledgers are read-only diagnostic projections. They are not physical
conservation laws and cannot rewrite the mainline.

## Acceptance intent

The new acceptance checks verify:

- `R` is defined as counter-structure and not residual.
- `Xi/Xin` is defined as unresolved residue carrier.
- Xi has no direct path to P or R.
- latent trajectories enter O candidate bridge before P/R.
- P/R tables are separate from legacy `pr_confirmation_graph_record`.
- source fact counts are unchanged.
- external ledgers are populated and status-reported.
- open issues remain recorded.
