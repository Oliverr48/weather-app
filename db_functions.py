# db_functions.py

import sqlite3

def get_weather_from_db(city, year, month):
    """Retrieve monthly precipitation (and optional max_temp) from SQLite."""
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_precipitation, rainy_days, max_temp
        FROM weather_data
        WHERE city=? AND year=? AND month=?
    """, (city, year, month))
    result = cursor.fetchone()
    conn.close()
    return result  # (total_precip, rainy_days, max_temp) or None

def save_weather_to_db(city, year, month, total_precip, rainy_days, max_temp):
    """Save monthly precipitation (and optional max_temp) into SQLite."""
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO weather_data (city, year, month, total_precipitation, rainy_days, max_temp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (city, year, month, total_precip, rainy_days, max_temp))
    conn.commit()
    conn.close()
