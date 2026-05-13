# Morphosphere v36.6 Full Materialized Deploy Pass4

This full-materialized package retains the original full-chain materialized output deployment while pruning redundant historical pass artifacts to keep the downloadable tar.zst below the practical 100 MB threshold.

Retained:
- v25-v34 base output DBs
- v35-v36.5 bridge / overlay DBs
- v36.5 full-chain materialized DB
- latest v36.6 pass3 process window and improvement DBs
- runtime_store historical payloads
- deployment scripts and manifests

Pruned:
- pass1/pass2 intermediate v36.6 DB duplicates
- embedded artifacts zip files that can be regenerated
- obsolete pass1/pass2 report duplicates

Fast checks are preserved via RUN_DEPLOY_CHECKS.sh. Heavy checks remain optional through existing optional scripts.
