# Pass7 Packaging Policy

Mode: full

Pass7 preserves the dual-package strategy:

- quick package: current v36.6 query/native-write readiness surface plus lightweight DBs.
- full-materialized package: retains full materialized base/runtime outputs while staying below the download-risk threshold where possible.

Normalized hypernode direct candidates remain candidates; raw direct FK is not overclaimed.
