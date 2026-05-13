# Quickstart: v0.9 Real Data Review

From the package root:

```bash
./run_local_realdata_review.sh
```

To run with your own physical CSV:

```bash
python3 -S morphosphere_v2pp/scripts/run_realdata_review_v09.py \
  --db outputs/morphosphere_realdata_review_v09_output_database.db \
  --report-dir morphosphere_v2pp/reports \
  --data-dir morphosphere_v2pp/data \
  --external-csv path/to/real_physical_samples.csv \
  --declare-real-external

python3 -S morphosphere_v2pp/scripts/run_realdata_review_acceptance_v09.py \
  outputs/morphosphere_realdata_review_v09_output_database.db
```

The candidate patch remains staged unless a human explicitly reviews and applies it outside this diagnostic layer.
