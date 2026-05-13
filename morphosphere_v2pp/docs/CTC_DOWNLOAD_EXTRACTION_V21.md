# CTC Download + Centroid Extraction v2.1

## Purpose

v2.1 closes the gap between a CTC data-source directory and a real local ingestion workflow. It does **not** bundle the public CTC dataset ZIP. Instead, it provides the downloader, MD5 verification, centroid extraction schema, and real-data readiness gates.

## Selected dataset

Primary dataset: `Fluo-N2DH-GOWT1`.

Reason: it is small enough for first real-data trials and directly tests bottom-layer motion-state extraction through centroids and trajectories.

## Boundary

CTC centroids are external observations. They do not overwrite `spacetime_cell`, `information_fiber`, or `raw_event_stream`. They are projection evidence for trajectory/O/P/R/Xi review.

## Real-data rule

Only run with `--declare-real-external` after you downloaded the CTC ZIP or otherwise produced centroid CSV from a traceable public/experimental source.
