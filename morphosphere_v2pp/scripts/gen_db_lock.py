#!/usr/bin/env python3
"""Generate a frozen lock file for a Morphosphere database.

Records SHA256 hash, all table schemas, and row counts.
This serves as provenance evidence for §14 data discipline.

Usage:
    python scripts/gen_db_lock.py db/v37490_ab_test.db
"""
import hashlib, json, sqlite3, sys
from pathlib import Path
from datetime import datetime, timezone


def generate_lock(db_path: str) -> dict:
    """Generate a lock manifest for the given database."""
    p = Path(db_path)
    if not p.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    # SHA256 of the entire file
    sha = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    conn = sqlite3.connect(str(p))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

    table_info = {}
    total_rows = 0
    for tbl in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
        schema = conn.execute(
            f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (tbl,)
        ).fetchone()[0]
        table_info[tbl] = {
            "row_count": count,
            "schema": schema,
        }
        total_rows += count

    conn.close()

    return {
        "database": p.name,
        "sha256": sha.hexdigest(),
        "size_bytes": p.stat().st_size,
        "total_tables": len(tables),
        "total_rows": total_rows,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "version": "v37.4.91",
        "tables": table_info,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python gen_db_lock.py <database.db>")
        sys.exit(1)

    db_path = sys.argv[1]
    lock = generate_lock(db_path)

    # Write lock file next to the database
    lock_path = Path(db_path).with_suffix(".lock.json")
    with open(lock_path, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2, ensure_ascii=False)

    print(f"Lock file: {lock_path}")
    print(f"  SHA256:  {lock['sha256'][:16]}...")
    print(f"  Tables:  {lock['total_tables']}")
    print(f"  Rows:    {lock['total_rows']}")
    print(f"  Size:    {lock['size_bytes'] / 1024:.0f} KB")


if __name__ == "__main__":
    main()
