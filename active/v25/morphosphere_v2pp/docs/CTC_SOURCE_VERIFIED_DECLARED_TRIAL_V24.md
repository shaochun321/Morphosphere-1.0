# CTC Source-Verified Declared Trial v2.4

This layer uses the uploaded original `Fluo-N2DH-GOWT1.zip` CTC source archive, extracts centroids from `*_GT/TRA/man_track###.tif`, and runs the declared-real CTC trial path.

Boundary:
- Source ZIP is included under `external_data/ctc/Fluo-N2DH-GOWT1.zip`.
- Extracted centroids are written to `morphosphere_v2pp/data/ctc_centroids_real_v24.csv`.
- The trial gate is `PASS_REAL_EXTERNAL_DECLARED`.
- Source facts are not rewritten.
- P/R remains before Xi; Xi does not replace P/R.
- No hot-swap or candidate parameter application is performed.

Re-extraction requires Pillow and NumPy:

```bash
python3 morphosphere_v2pp/scripts/extract_ctc_centroids_fast_v24.py \
  --zip external_data/ctc/Fluo-N2DH-GOWT1.zip \
  --out-csv morphosphere_v2pp/data/ctc_centroids_real_v24.csv
```

Validation:

```bash
./run_local_ctc_source_verified_v24.sh
```
