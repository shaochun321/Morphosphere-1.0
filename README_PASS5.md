# Morphosphere v36.6 Pass5

Pass5 formalizes quick/full deployment modes, package retention policy, module operation status, and module collaboration matrix.

Run:

```bash
./RUN_DEPLOY_CHECKS.sh
./RUN_V366_PASS5_CHECKS.sh
./RUN_PASS5_MODULE_STATUS.sh
```

For the full materialized package:

```bash
./RUN_PASS5_FULL_DATA_AUDIT.sh
```

Boundaries:

- Stage 2 bypass is allowed when current neural-substrate construction is carried by T/O/P/R/Xin, storage, ledger, and external modules.
- Materialization confidence is not truth, importance, or scientific validity.
- Direct FK is never faked; proxy/inferred backprojection remains labelled.
