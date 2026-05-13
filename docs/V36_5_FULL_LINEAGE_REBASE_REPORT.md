# Morphosphere v36.5 Full-Lineage Rebase Candidate Report

## Status

This is a **FULL_LINEAGE_REBASE_CANDIDATE** package. It is not a single-layer overlay and not a blueprint-only artifact.

## Components merged

| Component | Type | Source | Status |
|---|---|---|---|
| v25-v34 base | FULL_BASE | Morphosphere_v34 lineage, practically sourced from extracted v36.5 tree | present |
| v35-to-v36.4 bridge rollup | ENGINEERED_BRIDGE_ROLLUP | Morphosphere_v35_to_v36_4_bridge_rollup.tar.zst | applied |
| v36.5 semantic stripping / external readout | ENGINEERED_BRIDGE_OVERLAY | Morphosphere_v36_5.tar.zst | present |
| v36.5 full rebase metadata | REBASE_METADATA | this package | added |

## Coverage

The final tree contains active directories and SQLite DBs for v25-v36.5, plus the full-lineage rebase metadata DB.

Important bridge coverage restored:

- v35 attentional path integral governance
- v35H hyperedge incidence sidecar
- v36 dissipative metric bridge
- v36.1 variational external ledger bridge
- v36.2 variational action revision bridge
- v36.3 spacetime band bridge
- v36.4 constrained variational coupler bridge
- v36.5 semantic stripping / external readout control plane

## Boundaries

- Source facts are not rewritten.
- v35H remains a sparse incidence sidecar, not a native hypergraph database.
- v36 metric/action layers remain proxy layers, not physical metric or action claims.
- Semantic readout remains external/read-only.
- Xin direct-to-P/R promotion remains blocked.

## Local verification

```bash
./RUN_EXAMPLES.sh
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
python3 active/v365_full_rebase/scripts/query_v365_full_rebase.py --db outputs/m365_full_rebase.db --table coverage
```

## Note

This rebase candidate is intentionally explicit about provenance. The previously generated single-layer overlays remain valid as bridge artifacts, but this package is the first full-lineage candidate that contains the full base plus v35-v36.4 bridges and v36.5 semantic overlay in one tree.
