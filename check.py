import sqlite3

conn = sqlite3.connect("travel.db")
cur = conn.cursor()

cur.execute("PRAGMA table_info(travel_details)")
print("travel_details columns:")
for col in cur.fetchall():
    print(col)

cur.execute("PRAGMA table_info(transport_details)")
print("\ntransport_details columns:")
for col in cur.fetchall():
    print(col)

conn.close()
