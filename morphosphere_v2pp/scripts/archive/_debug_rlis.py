import sqlite3
# Check batch6 DB from last successful run
conn = sqlite3.connect('v37415_20260509_batch6.db')

# Check cross-domain transport edge types
print("edge_type values:")
for r in conn.execute("SELECT edge_type, COUNT(*) FROM transport_current_edge GROUP BY edge_type"):
    print(f"  {r[0]}: {r[1]}")

# Check for NoneType issue - look at last lines of batch6 runner output
print("\nrun_manifest:")
for r in conn.execute("SELECT run_id, notes FROM run_manifest").fetchall():
    print(f"  {r[0]}: {r[1][:100]}")
