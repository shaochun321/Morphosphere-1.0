# Morphosphere v2.5 Evidence Reconstruction Store - Quickstart

Boundary: diagnostic evidence reconstruction from v2.4. This is not final biology and not a strict scientific_run. SQLite is ledger/index; runtime_store holds evidence payloads.

Run locally:

```bash
cd morphosphere_v25_full_chain
./run_local_evidence_v25.sh
```

Explain one judgment:

```bash
python3 morphosphere_v2pp/scripts/explain_decision_v25.py --id p25_01-1_000_f000_027 --limit-points 4
```

Expected counts: information points 4575; coordinate transforms 4575; trajectory windows 532; P/R/Xi rows 532 each; evidence bundles 532; attention-yield events 262; recipes 7.

If source data is provided as parts:

```bash
cat ../ms25_src.part* > external_data/ctc/Fluo-N2DH-GOWT1.zip
```
