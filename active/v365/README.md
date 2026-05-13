# Morphosphere v36.5 - Semantic Stripping + External Readout Control Plane

v36.5 is a minimal runnable governance layer built on the v34 package. It does not rewrite source facts or previous P/R/Xi outputs.

Core rule:

```text
Upper recursion does not define explicit semantics.
Mainline stores carriers, measures, support, ledger refs, envelope refs and reentry policies.
External modules may read and classify, but cannot write back into the mainline.
```

Run:

```bash
python3 active/v365/scripts/build_v365.py --base-db outputs/m34.db --out-db outputs/m365.db
python3 active/v365/scripts/check_v365.py --db outputs/m365.db
python3 active/v365/scripts/query_v365.py --db outputs/m365.db --limit 3
python3 active/v365/scripts/audit_semantic_contamination.py --db outputs/m365.db
```

Boundary:

```text
semantic_label_in_mainline = 0
external_readout_can_write_mainline = 0
xin_definition_inside_mainline = 0
xin_direct_to_P_allowed = 0
xin_direct_to_R_allowed = 0
source_facts_rewritten = 0
```
