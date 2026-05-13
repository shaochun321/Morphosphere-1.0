# CTC Download + Centroid Extraction v2.1

This layer turns the v2.0 CTC data direction into a reproducible local workflow:

1. Download the selected CTC ZIP with `download_ctc_dataset_v21.py`.
2. Verify the Zenodo MD5.
3. Extract centroid rows from CTC TRA/SEG masks with `extract_ctc_centroids_v21.py`.
4. Run `run_ctc_download_extraction_v21.py --external-csv <centroids.csv> --declare-real-external` only for a real downloaded CTC-derived CSV.

The bundled `ctc_centroid_sample_v21.csv` is a local sample for pipeline validation and is not real external data.
