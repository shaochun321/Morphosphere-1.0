# Quickstart: Field Stream Reader v1.3

```bash
cd morphosphere_field_stream_v13_package
./run_local_field_stream_v13.sh
```

Rebuild only v1.3:

```bash
python3 -S morphosphere_v2pp/scripts/run_field_stream_adapter_v13.py   --db outputs/morphosphere_field_stream_v13_output_database.db   --runtime-dir runtime_store/v12   --report-dir morphosphere_v2pp/reports

python3 -S morphosphere_v2pp/scripts/run_field_stream_acceptance_v13.py   outputs/morphosphere_field_stream_v13_output_database.db
```
