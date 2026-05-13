# Streaming Queue + Backpressure Runtime v1.4

This append-only layer turns `field_stream_event_v13` into a bounded runtime queue with latency accounting, drop compensation, and queue-level P/R/Xi diagnostic responses.

## Boundary

- SQLite remains the ledger, not the runtime engine.
- Source fact tables are not rewritten.
- Field chunks from v1.2 are not rewritten.
- Candidate weights are not hot-swapped.
- P/R remains before Xi.
- The queue stores non-semantic event flow; it does not introduce labels.

## Runtime sidecar

The generated sidecar lives at `runtime_store/v14` and includes:

- `streaming_queue_manifest_v14.json`
- `queue_event_sample_v14.jsonl`
- `queue_dispatch_sample_v14.jsonl`
- `backpressure_tick_state_v14.jsonl`
- `queue_pr_xi_response_v14.jsonl`

## Purpose

v1.4 models a realistic streaming problem: external field chunks may produce more events than the online sensorium can dispatch in one tick. The system must handle queue depth, delay, backpressure, controlled loss, and compensation without pretending the lost signal never existed.
