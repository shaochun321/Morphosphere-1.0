# v34 Proxy × External Entropy Control Plane

This layer fuses proxy governance with the external entropy ledger. It does not rewrite source facts, does not allow hot-swap, and does not allow external ledger terms to steer P/R/Xi directly.

Run:

```bash
python3 active/v34/scripts/check_v34.py --db outputs/m34.db
python3 active/v34/scripts/query_v34.py --db outputs/m34.db --proxy-id px34_divergence_proxy
```
