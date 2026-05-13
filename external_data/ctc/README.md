# External CTC source placement

The raw CTC source ZIP is intentionally not bundled in this merged baseline.
Place it here if a source-level replay is required:

  external_data/ctc/Fluo-N2DH-GOWT1.zip

Expected SHA256:
  1a7bd9a7d1d10c4122c7782427b437246fb69cc3322a975485c04e206f64fc2c

The v25/v26/v27 audit and query checks do not require this ZIP, because the extracted
information points, coordinate transforms, trajectory windows, measures, and query
indexes are already materialized in outputs/ and runtime_store/.
