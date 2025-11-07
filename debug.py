import sqlite3

conn = sqlite3.connect("instance/barberia.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("🧩 Tablas:")
for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    print("-", row[0])

print("\n📋 Datos de 'servicios':")
for row in cursor.execute("SELECT * FROM servicio"):
    print(dict(row))

conn.close()
