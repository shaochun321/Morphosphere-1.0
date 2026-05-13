# Morphosphere v36.5 Full-Lineage Rebase Candidate

This package is a full-lineage rebase candidate. It combines:

1. v25-v34 full base lineage, practically sourced from the extracted v36.5 tree that already contained v25-v34 plus semantic overlay.
2. v35-to-v36.4 engineered bridge rollup.
3. v36.5 semantic stripping / external readout overlay.
4. v36.5 full-lineage rebase metadata and acceptance checks.

Artifact type: `FULL_LINEAGE_REBASE_CANDIDATE`.

It is not a single-layer overlay and not a blueprint-only artifact.

## Run

```bash
./RUN_EXAMPLES.sh
python3 active/v365_full_rebase/scripts/check_v365_full_rebase.py --db outputs/m365_full_rebase.db
```
