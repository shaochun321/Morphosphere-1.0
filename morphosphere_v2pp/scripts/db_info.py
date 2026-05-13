#!/usr/bin/env python3
"""Display table statistics for Morphosphere databases."""
import sqlite3, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # morphosphere_v2pp/
DB_DIR = ROOT / "db"

# Auto-discover all .db files
db_files = sorted(DB_DIR.glob("*.db")) if DB_DIR.exists() else []
if not db_files:
    print("No databases found in db/")
    sys.exit(1)

for db_path in db_files:
    size_kb = db_path.stat().st_size / 1024
    conn = sqlite3.connect(str(db_path))
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur]
    total = 0
    print(f"\n=== {db_path.name} ({size_kb:.0f} KB) ===")
    for t in sorted(tables):
        c = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        total += c
        print(f"  {t}: {c} rows")
    print(f"  --- Total: {total} rows across {len(tables)} tables ---")
    conn.close()
