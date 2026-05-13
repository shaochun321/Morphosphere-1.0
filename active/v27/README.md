# Morphosphere v2.7 - Measure Field Materialization + Reversible Query

This package reconstructs the v2.7 layer described in the uploaded chat.3.txt report:

- materialize P/R/Xi evidence into a 4D measure-field index
- preserve links to v2.5 information points, coordinate transforms, trajectory windows, calculation recipes, and external ledger refs
- provide reversible query CLI for point, trajectory, and measure ids

Boundary: this is diagnostic/audit infrastructure. It does not claim final biology or scientific_run.

## Run

```bash
./run.sh
python3 scripts/query_v27.py --db outputs/m27.db --point-id ip25_01_t000_trk01-1 --limit 5
python3 scripts/query_v27.py --db outputs/m27.db --trajectory-id tw25_01-1_000_f000_027 --limit 5
python3 scripts/query_v27.py --db outputs/m27.db --measure-id p25_01-1_000_f000_027 --limit 5
```

## Counts

- v27_measure_point_sample: 13725
- v27_measure_field_cell: 13725
- v27_reversible_query_index: 11278
- v27_acceptance_report: 10 checks

## Source

Built from v25 evidence reconstruction database. Original CTC source ZIP is not included; v25 already contains source points and provenance refs.
