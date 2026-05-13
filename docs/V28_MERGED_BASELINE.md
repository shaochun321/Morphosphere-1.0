# Morphosphere v28 Merged Baseline

This package merges source-lineage restoration plus active v25/v26/v27 and the v28 Shadow-Evidence Divergence Gate.

Active chain:

```text
v25 Evidence Reconstruction Store
  -> v26 Shadow Cell-Sphere Reconstruction
  -> v27 Measure Field / Reversible Query
  -> v28 Shadow-Evidence Divergence Gate
```

v28 aligns Evidence edges and Shadow edges by source point-pair, decomposes divergence, and records confirmed P, shadow overreach, evidence surprise/Xi, and emergence alert candidates.

Important boundary: v26 Shadow was built from v25 Evidence, so topological mismatch is expected to be low in this package. The primary real divergence in this build is measure-strength divergence, not missing-edge divergence. That is why v28 records many confirmed overlaps and shadow overreach/measure-drift rows rather than claiming a fully independent physical prediction test.

Run:

```bash
./CHECK_BASELINE.sh
./RUN_EXAMPLES.sh
python3 active/v28/scripts/query_v28.py --db outputs/m28.db --point-id ip25_01_t000_trk01-1 --limit 3
```

No CTC source ZIP and no historical source-package ZIPs are embedded.
