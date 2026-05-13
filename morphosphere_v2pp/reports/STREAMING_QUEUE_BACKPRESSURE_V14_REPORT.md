# Streaming Queue + Backpressure Runtime v1.4

This append-only layer turns field stream events into a bounded runtime queue with backpressure, latency accounting, drop compensation, and P/R/Xi diagnostic responses.

## Boundary

- SQLite remains ledger-only.
- Source facts and v1.2 field chunks are not rewritten.
- Candidate profiles are not hot-swapped.
- P/R remains before Xi.
- Semantic labels are not introduced.

## Counts

- queue events: 640
- dispatched events: 504
- dropped events: 88
- compensation records: 88
- replay scenarios: 9

## Baseline

- average P stability proxy: 0.515006
- average R counter proxy: 0.161120
- average Xi pressure proxy: 0.340701
- average latency ms: 9.765625
- backpressure ticks: 9
