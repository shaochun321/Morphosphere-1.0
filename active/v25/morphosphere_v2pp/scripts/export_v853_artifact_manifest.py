#!/usr/bin/env python3
"""Export v8.5.3 release artifact fingerprints into the diagnostic DB.

Diagnostic-only. Does not mark scientific_run and does not create v8.6/v9.
"""
from __future__ import annotations
import hashlib
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "v85_full_diagnostic_run.db"
MIGRATION = ROOT / "migrations" / "014_v853_hardening_reproducibility.sql"
ARTIFACTS = [
    # Do not self-hash v85_full_diagnostic_run.db into the same DB: writing the
    # manifest mutates the DB and immediately makes that hash stale. The packaged
    # output DB is checksummed externally by BUILD_METADATA.json and the .sha256 file.
    ("validation_config", "configs/v853_validation.json", True),
    ("validation_report", "reports/V853_VALIDATION_REPORT.md", True),
    ("validation_summary", "reports/v853_validation_summary.json", True),
    ("alignment_migration", "migrations/015_v853_alignment_exports.sql", True),
    ("behavioral_acceptance", "scripts/run_v853_behavioral_acceptance.py", True),
    ("quickstart", "QUICKSTART_V853.md", True),
    ("release_notes", "FINAL_RELEASE_NOTES_V853.md", True),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not DB.exists():
        print(f"DB not found: {DB}")
        return 2
    conn = sqlite3.connect(DB)
    conn.executescript(MIGRATION.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM v853_release_artifact_manifest WHERE release_version='v8.5.3-hardening'")
    inserted = 0
    for role, rel, included in ARTIFACTS:
        path = ROOT / rel
        if not path.exists():
            print(f"SKIP missing artifact: {rel}")
            continue
        conn.execute(
            """
            INSERT INTO v853_release_artifact_manifest
            (artifact_id,release_version,artifact_role,artifact_path,size_bytes,sha256,included_in_package,created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            ("art_" + uuid.uuid4().hex[:10], "v8.5.3-hardening", role, rel, path.stat().st_size,
             sha256_file(path), 1 if included else 0, now()),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"exported_artifacts={inserted}")
    return 0 if inserted >= 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
