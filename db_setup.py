import sqlite3

conn = sqlite3.connect("weather.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        city TEXT NOT NULL,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        total_precipitation REAL NOT NULL,
        rainy_days INTEGER NOT NULL,
        max_temp REAL,  -- NEW COLUMN to store max temperature
        UNIQUE (city, year, month)
    )
""")

conn.commit()
conn.close()
print("Database initialized successfully!")
