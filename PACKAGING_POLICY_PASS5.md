# Packaging Policy Pass5

Pass5 keeps two deployment modes:

- quick deploy: lightweight current v36.6 inspection and fast checks.
- full materialized deploy: retained v25-v34 base outputs, runtime_store, full materialized data, and current v36.6 DBs.

Historical pass1/pass2 intermediate artifacts are not required in the deployable package because pass3/pass5 supersede them and scripts are included for regeneration.
