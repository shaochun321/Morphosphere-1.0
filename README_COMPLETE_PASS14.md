# Morphosphere v36.6 Complete Deploy Pass14

This is the complete deployable package assembled from the full materialized Pass12 recovery tree plus Pass13 native-shaped replay outputs.

## What this package contains

- v25-v34 base outputs and runtime_store payloads retained from the full materialized lineage tree.
- v35-v36.5 bridge / overlay DBs and full lineage rebase DB.
- v36.5 full-chain materialized DB.
- v36.6 process_window materialization and pass3 improvement outputs.
- Pass10 implementation coverage audit.
- Pass11 parallel workbench.
- Pass12 native-shaped skeleton and offline stress projection outputs.
- Pass13 native-shaped replay sample outputs.
- Query scripts and deployment/check scripts.

## Important boundary

This is a complete **materialized integration + native-shaped replay** package. It does not claim to be an online native life runtime, a real PDE/continuous field implementation, or a true native synchronous full-chain runtime. It retains historical base/runtime data and the latest replay/stress/coverage artifacts.

## Recommended checks

```bash
./RUN_DEPLOY_CHECKS.sh
./RUN_PASS14_COMPLETE_CHECKS.sh
./RUN_PASS13_REPLAY_SUMMARY.sh
```

## Key DBs

- `outputs/m25.db` through `outputs/m34.db`: historical/base evidence and runtime lineage outputs.
- `outputs/m365_full_rebase.db`: full lineage rebase coverage proof.
- `outputs/v366/m365_full_chain_materialized.db`: full-chain materialized index.
- `outputs/v366/m366_process_window_pass3.db`: v36.6 process_window materialization.
- `outputs/v366/m366_implementation_coverage_audit.db`: Pass10 implementation coverage audit.
- `outputs/v366/m366_build_pass12_execution.db`: Pass12 native-shaped skeleton and stress projection output.
- `outputs/v366/m366_build_pass13_native_replay.db`: Pass13 native-shaped replay sample output.
```
