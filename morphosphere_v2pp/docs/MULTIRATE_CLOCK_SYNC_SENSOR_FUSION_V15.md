# Multi-Rate Clock Synchronization + Sensor Fusion Adapter v1.5

Version: `multi_rate_clock_sync_sensor_fusion_v1.5`

This layer repairs the v1.4 queue ledger from the valid v1.3 baseline, then appends a multi-rate synchronization and sensor-fusion adapter. It keeps SQLite as a ledger, not a high-rate runtime engine.

## Purpose

Different modalities do not share a perfect clock. Field chunks, mechanical force, acoustic pressure, optical intensity, device-edge conductance, and preneural ticks are resampled into canonical `system_clock_entry` frames.

## Core chain

```text
field_stream_event_v13
  -> repaired bounded queue v14
  -> multirate sensor samples
  -> clock alignment observations
  -> resampled sync frames
  -> phase alignment states
  -> cross-modal bindings
  -> fused sensor events
  -> fusion P/R/Xi response
```

## Boundaries

- No source fact rewrite.
- No hot-swap of fitted parameters.
- P/R remains before Xi.
- Fusion is semantic-label-free.
- SQLite stores ledger rows, not live high-rate buffers.

## Key counts

- clock domains: 7
- multirate sensor samples: 122
- sync frames: 10
- cross-modal bindings: 50
- fused events: 50
- replay scenarios: 10

## Honest boundary

This is not a real sensor bus, not a real-time operating system, and not a scientific-run multi-sensor calibration. It is an append-only diagnostic adapter that proves the project can represent clock drift, resampling, phase alignment, and fusion pressure without corrupting source facts.
