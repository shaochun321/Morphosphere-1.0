# v27 merged baseline notes

This package merges the short restored-lineage baseline with the current chat's reconstructed v27 measure-field materialization package.

## Why v27 is based on v25

v25 is the evidence reconstruction source-of-truth: information points, coordinate transforms, trajectory windows, P/R/Xi measures, recipes, and evidence bundles. v27 materializes these measures into reversible query indexes. v26 is a shadow cell-sphere branch derived from the same v25 evidence. Therefore the intended topology is:

```text
v25 evidence -> v27 reversible measure field
v25 evidence -> v26 shadow cell-sphere
```

## What is not embedded

- raw `Fluo-N2DH-GOWT1.zip`
- historical original source-package ZIP files
- `__pycache__` / `.pyc`

References and SHA256 metadata for original packages are in `lineage/source_package_refs/`.
