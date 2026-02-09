import sqlite3
from pathlib import Path

db_path = Path("metadata/database/romfarmer.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get distinct system names
cursor.execute("SELECT DISTINCT system FROM scraped_games")
systems = cursor.fetchall()

print("Systems in database:")
for system in systems:
    print(f"- {system[0]}")

# Check count for 'gb' and 'gameboy'
cursor.execute("SELECT COUNT(*) FROM scraped_games WHERE system = 'gb'")
gb_count = cursor.fetchone()[0]
print(f"\nCount for 'gb': {gb_count}")

cursor.execute("SELECT COUNT(*) FROM scraped_games WHERE system = 'gbc'")
gbc_count = cursor.fetchone()[0]
print(f"Count for 'gbc': {gbc_count}")

cursor.execute("SELECT COUNT(*) FROM scraped_games WHERE system = 'gba'")
gba_count = cursor.fetchone()[0]
print(f"Count for 'gba': {gba_count}")

# Check count for 'msx1'
cursor.execute("SELECT COUNT(*) FROM scraped_games WHERE system = 'msx1'")
msx1_count = cursor.fetchone()[0]
print(f"Count for 'msx1': {msx1_count}")

conn.close()
