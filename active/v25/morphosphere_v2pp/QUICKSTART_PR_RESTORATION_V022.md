# Quickstart: P/R Restoration + Xi Boundary Repair v0.2.2

Run the full local validation:

```bash
./run_local_pr_restoration.sh
```

Or run the restoration layer manually:

```bash
cd morphosphere_v2pp
python -S scripts/run_pr_restoration_v022.py \
  --db ../outputs/morphosphere_pr_restoration_v022_output_database.db \
  --report-dir reports

python -S scripts/run_pr_restoration_acceptance_v022.py \
  ../outputs/morphosphere_pr_restoration_v022_output_database.db
```

Expected acceptance:

```text
v8.5.2 SQL acceptance: PASS
v8.5.3 behavioral acceptance: PASS
state_separation_v0.1 acceptance: PASS
dynamic_recursive_v0.2 acceptance: 39/39 PASS
pr_restoration_v0.2.2 acceptance: 34/34 PASS
```

Main chain:

```text
raw_event_stream
  -> origin_anchor
  -> latent_trajectory / T-trace
  -> O_candidate_bridge
  -> P/R decomposition
  -> Xi boundary guard
```

Boundary rule:

```text
R = Refutational Counter-Structure, not residual.
Xi/Xin = Unresolved Residue Carrier, not P/R replacement.
Xi may re-enter only through O_candidate_bridge.
```
