#!/usr/bin/env python3
"""Extract the two SQL results and write to a plain-text report."""
import sqlite3, json, os, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT = str(BASE / "NECROPOLIS_SQL_RESULTS.txt")

lines = []

def p(s=""):
    lines.append(s)
    print(s)

# ═══════════════════════════════════════════════════════════════════
# 第一刀: SELECT node_uid, death_reason, dna_snapshot_json
#         FROM pipe_stress_node_necropolis LIMIT 1;
# ═══════════════════════════════════════════════════════════════════
db1 = str(BASE / "db" / "v37495_necropolis_stress.db")
conn1 = sqlite3.connect(db1)
conn1.row_factory = sqlite3.Row

p("=" * 72)
p("SQL Query #1  (第一刀: 法医尸检报告)")
p("=" * 72)
p()
p("  SQL:")
p("    SELECT node_uid, death_reason, dna_snapshot_json")
p("    FROM pipe_stress_node_necropolis")
p("    LIMIT 1;")
p()
p("-" * 72)
p("  RESULT:")
p("-" * 72)

row = conn1.execute(
    "SELECT node_uid, death_reason, dna_snapshot_json "
    "FROM pipe_stress_node_necropolis LIMIT 1"
).fetchone()

if row:
    p(f"  node_uid:          {row['node_uid']}")
    p(f"  death_reason:      {row['death_reason']}")
    p(f"  dna_snapshot_json:")
    dna = json.loads(row["dna_snapshot_json"])
    for line in json.dumps(dna, indent=4, ensure_ascii=False).splitlines():
        p(f"    {line}")
else:
    p("  (no rows)")

# Also show a few more for context
p()
p("-" * 72)
p("  BONUS: First 5 rows (summary)")
p("-" * 72)
rows = conn1.execute(
    "SELECT node_uid, death_reason, dna_snapshot_json "
    "FROM pipe_stress_node_necropolis LIMIT 5"
).fetchall()
for i, r in enumerate(rows):
    dna = json.loads(r["dna_snapshot_json"])
    p(f"  [{i+1}] node_uid={r['node_uid']}, "
      f"death_reason={r['death_reason']}, "
      f"dna_edges={len(dna)}")

total = conn1.execute("SELECT COUNT(*) FROM pipe_stress_node_necropolis").fetchone()[0]
p(f"  Total dead nodes in necropolis: {total}")
conn1.close()

# ═══════════════════════════════════════════════════════════════════
# 第二刀: oscillation regime from prx_decomp
# ═══════════════════════════════════════════════════════════════════
p()
p()
p("=" * 72)
p("SQL Query #2  (第二刀: 第五法则 oscillation)")
p("=" * 72)

db2 = str(BASE / "db" / "v37493_multi_pipeline.db")
if not os.path.exists(db2):
    p(f"  [DB NOT FOUND: {db2}]")
else:
    conn2 = sqlite3.connect(db2)
    conn2.row_factory = sqlite3.Row

    # Find the actual prx_decomp table name
    tables = [r[0] for r in conn2.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%prx_decomp%'"
    ).fetchall()]
    p()
    p(f"  Available prx_decomp tables: {tables}")

    for tbl in tables:
        cols = [c[1] for c in conn2.execute(f"PRAGMA table_info({tbl})").fetchall()]

        # Determine the regime column name
        regime_col = None
        if "regime_label" in cols:
            regime_col = "regime_label"
        elif "regime" in cols:
            regime_col = "regime"

        if not regime_col:
            p(f"  [{tbl}] no regime column found (cols={cols})")
            continue

        p()
        p(f"  SQL:")
        p(f"    SELECT * FROM {tbl}")
        p(f"    WHERE {regime_col} = 'oscillation'")
        p(f"    LIMIT 1;")
        p()
        p("-" * 72)
        p("  RESULT:")
        p("-" * 72)

        osc = conn2.execute(
            f"SELECT * FROM {tbl} WHERE {regime_col} = 'oscillation' LIMIT 1"
        ).fetchone()

        if osc:
            for col in cols:
                p(f"  {col:30s}: {osc[col]}")
        else:
            p("  (no oscillation rows)")

        # Count total oscillation
        cnt = conn2.execute(
            f"SELECT COUNT(*) FROM {tbl} WHERE {regime_col} = 'oscillation'"
        ).fetchone()[0]
        p()
        p(f"  Total oscillation records in {tbl}: {cnt}")

    conn2.close()

p()
p("=" * 72)
p("END OF REPORT")
p("=" * 72)

# Write to file
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

print(f"\n>>> Report written to: {OUT}")
