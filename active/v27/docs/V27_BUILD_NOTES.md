# v2.7 build notes

The uploaded original v2.7 report defines `measure_field_materialization_reversible_query_v2.7`: fields, real information points, coordinate data, trajectory windows, mathematical recipe traces, and P/R/Xi measures must be traceable, queryable, and reprojectable.

This package implements that goal on top of the current v25 evidence reconstruction DB. It preserves v25 tables and adds:

- `v27_measure_point_sample`
- `v27_measure_field_cell`
- `v27_reversible_query_index`
- `v27_measure_recipe_trace`
- `v27_reconstruction_query_sample`
- `v27_field_grid_spec`
- `v27_acceptance_report`

Design boundary: raw source reversibility and process replayability are preserved through v25/v27 references. Field inversion is support-domain reprojection, not raw-image inversion.
