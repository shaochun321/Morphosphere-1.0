# Morphosphere v33: Bottom Prediction Adapter

v33 reconnects legacy/internal bottom modules as prediction sources through the v32 generalized source adapter. It does not reactivate old code as authority and does not rewrite evidence/source facts.

Run:

```bash
python3 active/v33/scripts/check_v33.py --db outputs/m33.db
python3 active/v33/scripts/query_v33.py --db outputs/m33.db --adapter-id ad33_preneural_edge --limit 3
```
