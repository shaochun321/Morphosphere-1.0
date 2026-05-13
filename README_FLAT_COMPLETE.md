# Morphosphere v37.0 Native Runtime Prototype - Flat Complete Package

This is a flattened complete package. It does not contain nested `.tar.zst` or `.zip` payloads.

## Layout

- `outputs/`: original base DBs and v35-v36.5 overlays from the full lineage tree.
- `outputs/v366/`: v36.6 materialized integration, process window, stress/replay/audit DBs.
- `outputs/v367/`: v36.7 engineering hardening baseline DBs.
- `outputs/v368/`: v36.8 mainline functional integration and consolidated final DBs.
- `outputs/v370/`: v37.0 native runtime prototype DB.
- `runtime_store/`: base runtime payloads retained from the complete tree.
- `scripts/`: query and package integrity scripts.
- `docs/`: reports, blueprints, context compactions, data-only reviews.

## Checks

```bash
./RUN_FLAT_COMPLETE_CHECKS.sh
./RUN_V370_SUMMARY.sh
```

Expected key metrics:

- v368 mainline trace windows: 532
- v368 transition edges: 446
- v367 native anchor facts: 855
- v367 RMI default index rows: 11,530
- v370 runtime samples: 80
- v370 stage traces: 960
- nested compressed files: 0

## Boundary

This package is a flat complete materialized / prototype package. It does not claim:

- online native runtime
- true PDE/continuous field
- destructive migration of legacy DBs
- semantic writeback to mainline
- nested compressed bundle deployment
