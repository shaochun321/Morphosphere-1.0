-- Morphosphere v8.5.3 hardening: reproducibility and release manifest.
-- Additive diagnostic-only schema. Does not create v8.6/v9 and does not enable scientific_run.

CREATE TABLE IF NOT EXISTS v853_reproducibility_report (
    report_id TEXT PRIMARY KEY,
    current_perturbation_run_id TEXT NOT NULL,
    previous_perturbation_run_id TEXT,
    baseline_fingerprint TEXT NOT NULL,
    effect_signature_hash TEXT NOT NULL,
    max_abs_delta REAL NOT NULL,
    compared_metric_count INTEGER NOT NULL,
    tolerance REAL NOT NULL,
    passed INTEGER NOT NULL,
    diagnostic_message TEXT NOT NULL,
    forbidden_use TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS v853_release_artifact_manifest (
    artifact_id TEXT PRIMARY KEY,
    release_version TEXT NOT NULL,
    artifact_role TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    included_in_package INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
