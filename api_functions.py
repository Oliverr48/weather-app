# api_functions.py

import requests
from datetime import datetime
from calendar import monthrange
from db_functions import save_weather_to_db
from config import CITY_COORDINATES

def fetch_weather_from_api(city, year, month):
    """
    Fetch monthly precipitation from Open-Meteo's archive.
    Return (total_precip, rainy_days, max_temp).
    """
    latitude, longitude = CITY_COORDINATES[city]

    month_start = datetime(year, month, 1).strftime("%Y-%m-%d")
    month_end = datetime(year, month, monthrange(year, month)[1]).strftime("%Y-%m-%d")

    URL = (
        f"https://archive-api.open-meteo.com/v1/archive?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={month_start}&end_date={month_end}"
        f"&daily=precipitation_sum,temperature_2m_max&timezone=Australia/Perth"
    )

    response = requests.get(URL)
    if response.status_code == 200:
        data = response.json()

        total_precip = sum(
            float(p) for p in data["daily"]["precipitation_sum"]
            if p is not None
        )
        rainy_days = sum(
            1 for p in data["daily"]["precipitation_sum"]
            if p is not None and float(p) > 0
        )
        max_temp = None
        if "temperature_2m_max" in data["daily"]:
            # find monthly highest
            max_temp = max(
                float(t) for t in data["daily"]["temperature_2m_max"]
                if t is not None
            )

        # Save to DB so next time we avoid re-fetch
        save_weather_to_db(city, year, month, total_precip, rainy_days, max_temp)
        return total_precip, rainy_days, max_temp
    else:
        return None, None, None
