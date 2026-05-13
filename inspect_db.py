import sqlite3
db = sqlite3.connect('morphosphere_v2pp/v85_full_diagnostic_run.db')
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    table_name = t[0]
    schema = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    print(f"\nSchema for {table_name}:")
    for col in schema:
        print(f"  {col[1]} ({col[2]})")
    count = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  Row count: {count}")

db.close()
