import sqlite3

conn = sqlite3.connect("travel.db")
cur = conn.cursor()

print("Adding missing columns...")

# Get existing columns
cur.execute("PRAGMA table_info(travel_details)")
cols = [c[1] for c in cur.fetchall()]

def add(col, ddl):
    if col not in cols:
        cur.execute(f"ALTER TABLE travel_details ADD COLUMN {col} {ddl}")
        print(f"✔ Added column: {col}")
    else:
        print(f"✔ Column already exists: {col}")

add("days", "INTEGER DEFAULT 0")
add("country", "TEXT DEFAULT ''")
add("port", "TEXT DEFAULT ''")
add("total_cost", "REAL DEFAULT 0")

conn.commit()
conn.close()

print("Upgrade complete.")
