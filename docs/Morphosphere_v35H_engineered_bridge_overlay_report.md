# Morphosphere v35H Engineered Bridge Overlay (Rebuilt)

Artifact type: `ENGINEERED_BRIDGE_OVERLAY`  
Includes full base: `false`  
Not a full lineage package: `true`

This rebuilt v35H overlay restores the missing downloadable archive. It implements the lightweight Hyperedge Incidence Sidecar for v35 attention/path-integral relations without introducing a native hypergraph database, replacing SQLite, or persisting dense `N x E x T` tensors.

## Core tables

- `v35h_hypernode_registry`: 747
- `v35h_hyperedge_proposal`: 120
- `v35h_hyperedge_incidence`: 855
- `v35h_hyperedge_ledger_weight`: 120
- `v35h_hyperedge_gc_report`: 12
- `v35h_hyperedge_appeal_registry`: 10
- `v35h_runtime_manifest`: 3
- `v35h_acceptance_report`: 12 / 12 PASS

## Guardrails

- `native_hypergraph_db_enabled = 0`
- `sqlite_source_truth_retained = 1`
- `dense_tensor_persistent_forbidden = 1`
- `semantic_label_in_mainline = 0`
- `source_facts_rewritten = 0`
- `hyperedge_can_promote_truth = 0`

## Local use

```bash
tar --zstd -xf Morphosphere_v35H_engineered_bridge_overlay.tar.zst
cd Morphosphere_v35H_engineered_bridge_overlay
./RUN_EXAMPLES.sh
```

