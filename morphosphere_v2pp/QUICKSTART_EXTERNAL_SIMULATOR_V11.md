# Quickstart: External Simulator Adapter v1.1

Run from package root:

```bash
./run_local_external_simulator_v11.sh
```

Rebuild only v1.1:

```bash
python3 -S morphosphere_v2pp/scripts/run_external_simulator_adapter_v11.py \
  --db outputs/morphosphere_external_simulator_v11_output_database.db \
  --runtime-dir runtime_store/v11 \
  --report-dir morphosphere_v2pp/reports \
  --package-root .

python3 -S morphosphere_v2pp/scripts/run_external_simulator_acceptance_v11.py \
  outputs/morphosphere_external_simulator_v11_output_database.db
```
