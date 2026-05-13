# CTC Declared Real Trial v2.2

This layer orchestrates a conservative CTC real-data trial.

Default local run uses `ctc_centroid_sample_v21.csv` and **must remain blocked** as real external data.
It validates the pipeline without claiming that sample/demo data are real.

```bash
./run_local_ctc_declared_trial_v22.sh
```

For real CTC data:

1. Download `Fluo-N2DH-GOWT1.zip` according to `morphosphere_v2pp/data/ctc_download_manifest_v21.json`.
2. Extract centroids:

```bash
python3 -S morphosphere_v2pp/scripts/extract_ctc_centroids_v21.py \
  --zip external_data/ctc/Fluo-N2DH-GOWT1.zip \
  --out-csv morphosphere_v2pp/data/ctc_centroids_real_v22.csv
```

3. Run the declared trial:

```bash
python3 -S morphosphere_v2pp/scripts/run_ctc_declared_trial_v22.py \
  --db outputs/morphosphere_ctc_declared_trial_v22_output_database.db \
  --centroid-csv morphosphere_v2pp/data/ctc_centroids_real_v22.csv \
  --declare-real-external \
  --report-dir morphosphere_v2pp/reports \
  --package-root .
```

The runner is append-only. It does not rewrite `spacetime_cell`, `information_fiber`, `raw_event_stream`, or P/R/Xi source facts.
