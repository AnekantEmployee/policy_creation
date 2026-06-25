import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'compliance.db')
con = sqlite3.connect(db_path)
cur = con.cursor()

# List all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print(f"Tables: {tables}\n")

for table in tables:
    cur.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cur.fetchone()[0]
    print(f"  {table}: {count} rows")
    if count > 0 and count <= 20:
        cur.execute(f"SELECT * FROM [{table}] LIMIT 5")
        rows = cur.fetchall()
        cur.execute(f"PRAGMA table_info([{table}])")
        cols = [c[1] for c in cur.fetchall()]
        print(f"    cols: {cols}")
        for r in rows:
            print(f"    {r}")
    print()

con.close()
