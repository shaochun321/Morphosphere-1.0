# Morphosphere v36.6 Full-Chain Process Window Deployable Package

This deployable package contains the v36.5 full-lineage rebase engineering tree plus the v36.6 process-window/materialized-data additions generated in this run.

## What this package is

It is a complete offline deploy/run package for the currently implemented Morphosphere full-chain materialization:

- v25-v34 base outputs and runtime/data artifacts
- v35 attention bridge
- v35H hyperedge incidence sidecar
- v36-v36.4 variational / R-band / coupler bridge data
- v36.5 semantic stripping / Xin carrier / external readout output
- v36.5 full-chain materialized data index
- v36.6 process_window and hypernode_spacetime_backprojection layer
- v36.6 improvement pass 1: Stage 2 audit, preneural interface trace, counter/masking coverage, hypernode direct-FK upgrade candidates, process-window quality scoring

It is not an online living runtime. It is an offline deployable engineering package for full-chain data inspection, checks, and materialized outputs.

## Key entry points

```bash
tar --zstd -xf Morphosphere_v36_6_full_chain_process_window_deployable.tar.zst
cd Morphosphere_v36_6_full_chain_process_window_deployable
./RUN_DEPLOY_CHECKS.sh
./RUN_CORE_DB_INTEGRITY.sh
./RUN_V366_SUMMARY.sh
# Optional exhaustive bridge checks:
RUN_FULL_BRIDGE=1 ./RUN_FULL_OPTIONAL_CHECKS.sh
```

Existing v36.5 checks are also preserved:

```bash
./RUN_EXAMPLES.sh
./RUN_FULL_BRIDGE_CHECKS.sh
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
python3 active/v365_full_rebase/scripts/query_v365_full_rebase.py --db outputs/m365_full_rebase.db --table coverage
```

## Important DBs

| Path | Role |
|---|---|
| `outputs/m25.db` | v25 evidence reconstruction alias |
| `outputs/m26.db` | v26 shadow reconstruction alias |
| `outputs/m34.db` | large base DB, main bottom/data/gov base used for materialization |
| `outputs/m35.db` | v35 attention overlay |
| `outputs/m35H.db` | v35H hyperedge incidence sidecar |
| `outputs/m36*.db` | v36-v36.4 bridge DBs |
| `outputs/m365.db` | v36.5 semantic stripping / external readout DB |
| `outputs/m365_full_rebase.db` | full-lineage coverage / boundary / acceptance proof DB |
| `outputs/v366/m365_full_chain_materialized.db` | full-chain data materialization index |
| `outputs/v366/m366_process_window.db` | v36.6 process_window + hypernode backprojection DB |
| `outputs/v366/m366_improvement_pass1.db` | Stage 2 / preneural / masking / FK upgrade / quality pass DB |

Copies of the v36.6 DBs are also stored under `active/v366_process_window/db/`.

## v36.6 additions

The new v36.6 layer adds:

- `v366_process_window_registry`
- `v366_process_window_member`
- `v366_process_window_measure_binding`
- `v366_process_window_ledger_binding`
- `v366_hypernode_spacetime_backprojection`
- `v366_hyperedge_spacetime_relation`
- `v366_coordinate_nonlocal_proxy_audit`
- `stage2_object_surface_materialization_audit`
- `preneural_interface_operator_trace`
- `counter_masking_coverage_audit`
- `hypernode_direct_fk_upgrade_candidate`
- `process_window_quality_score`

## Boundary notes

- `process_window` is a new materialized working unit, not a replacement for raw source facts.
- Coordinates are hidden from mainline interpretation but retained for audit and backprojection.
- `hypernode_spacetime_backprojection` is currently mostly inferred/proxy, not direct FK.
- Semantic readout remains external and read-only.
- Xin direct-to-P/R remains blocked.
- External entropy ledger remains an audit/ledger layer, not a truth optimizer.

## Included context

See:

- `docs/v366_context/morphosphere_context_compaction_v366.md`
- `docs/v366_context/morphosphere_context_compaction_v366.docx`
- `docs/v366_context/Morphosphere_v36_6_semanticless_process_window_coordinate_hidden_blueprint.md`
- `active/v366_process_window/reports/`


## v36.6 Improvement Pass 2

Pass2 adds an additive materialization layer:

- `outputs/v366/m366_improvement_pass2.db`
- `outputs/v366/m366_process_window_pass2.db`
- `active/v366_process_window/reports/m366_improvement_pass2_report.md`

Run:

```bash
./RUN_V366_PASS2_CHECKS.sh
./RUN_V366_SUMMARY.sh
```

Pass2 does not rewrite source facts. It adds Stage-2 proxy bridge rows, R-chain concrete mask template bindings, preneural process-window supplements, hypernode FK upgrades where target rows exist, and process-window strengthening records.

## Pass3 update

Pass3 adds `m366_process_window_pass3.db`, which separates materialization confidence from architecture route legitimacy.

Run:

```bash
./RUN_V366_PASS3_CHECKS.sh
```

Interpretation:

- `materialization_confidence` = data linkage completeness.
- `architecture_route_legitimacy` = whether the process route is valid under the current architecture.
- Stage 2 bypass is legitimate when T/O/P/R/Xin + storage + ledger carries the current neural-like substrate.
