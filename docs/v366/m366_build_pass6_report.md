# Morphosphere v36.6 Pass6: Lineage Query Surface and Backtrace Pack

Generated: 2026-05-06T05:58:50Z

Pass6 turns the v36.6 materialized data into a practical query surface. It does not change source facts and does not claim online life runtime. It adds a fast lineage/backtrace layer so the deployable package can answer what data exists, how modules collaborate, and how a process window traces back to information points, T/O/P/R/Xin, ledger, attention/hyperedge, and readout.

## Key Counts

| Metric | Count |
|---|---:|
| lineage trace rows | 532 |
| backtrace samples | 20 |
| module health rows | 7 |
| collaboration edges | 10 |
| process windows | 1633 |
| process window members | 22128 |
| hypernode direct FK after normalization | 0 / 855 |
| high confidence windows | 120 |
| medium confidence windows | 671 |
| low confidence windows | 842 |

## CLI

```bash
python3 scripts/query_v366_lineage.py --db outputs/v366/m366_build_pass6.db status
python3 scripts/query_v366_lineage.py --db outputs/v366/m366_build_pass6.db health
python3 scripts/query_v366_lineage.py --db outputs/v366/m366_build_pass6.db samples --limit 3
python3 scripts/query_v366_lineage.py --db outputs/v366/m366_build_pass6.db trace --id pw_traj_tw25_01-1_000_f000_027
```

## Boundary

Stage 2 bypass remains legitimate when T/O/P/R/Xin + storage + ledger substrate is present. Materialization confidence is data-link completeness, not truth or importance. Hypernode backprojection remains explicitly direct/proxy/inferred.
