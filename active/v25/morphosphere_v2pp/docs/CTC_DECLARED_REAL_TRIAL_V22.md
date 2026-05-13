# CTC Declared Real Trial v2.2

v2.2 closes the gap between a prepared CTC extraction tool and a declared real-data trial.

## Modes

- **Dry-run / sample mode**: uses bundled centroid sample and remains blocked from real-data claims.
- **Declared real external mode**: requires user-downloaded or uploaded CTC centroid CSV and `--declare-real-external`.
- **Raw ZIP/root extraction mode**: can call the v2.1 centroid extractor before running the trial.

## Data Philosophy

CTC data are not allowed to overwrite the bottom cell sphere. They enter as external motion observations and produce projection evidence:

```text
CTC centroid tracks -> motion features -> cell mapping -> motion projection -> P/R/Xi trial response
```

P/R remains before Xi. Xi can only carry unresolved motion residue after P/R.

## Realness Guard

Sample, demo, or high-fidelity synthetic inputs cannot be declared real external data. The v2.2 gate blocks false real claims.
