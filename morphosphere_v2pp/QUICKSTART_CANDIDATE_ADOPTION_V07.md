# Quickstart: v0.7 Candidate Adoption Gate

Run all v0.7 checks:

```bash
./run_local_candidate_adoption.sh
```

Rebuild only v0.7:

```bash
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_v07.py --db outputs/morphosphere_candidate_adoption_v07_output_database.db --report-dir morphosphere_v2pp/reports
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_acceptance_v07.py outputs/morphosphere_candidate_adoption_v07_output_database.db
```

Provide external physical data:

```bash
python3 -S morphosphere_v2pp/scripts/run_candidate_adoption_v07.py --db outputs/morphosphere_candidate_adoption_v07_output_database.db --calibration-csv path/to/samples.csv --report-dir morphosphere_v2pp/reports
```
