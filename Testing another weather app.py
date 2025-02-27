import requests
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt  # Correct import for plotting
from calendar import monthrange

# =======================
# Part 1: Existing Forecast/Archive Weather Data
# =======================

# Step 1: Define city coordinates
CITY_COORDINATES = {
    "perth": (-31.95, 115.86),
    "sydney": (-33.87, 151.21),
    "melbourne": (-37.81, 144.96),
    "brisbane": (-27.47, 153.03),
    "adelaide": (-34.93, 138.60),
}

# Step 2: Get User Input for city
CITY = input("Enter City Name (Perth, Sydney, Melbourne, etc.): ").strip().lower()

# Step 3: Check if the city is valid
if CITY not in CITY_COORDINATES:
    print("\n❌ City not found. Please enter a valid city name from the list.")
    exit()

latitude, longitude = CITY_COORDINATES[CITY]

# Step 4: Validate Date Input (for temperature forecast/archive)
def validate_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

# Loop until valid dates are entered
while True:
    # Prompt user to enter start date
    start_date = input("Enter start date (YYYY-MM-DD): ")
    # Prompt user to enter end date
    end_date = input("Enter end date (YYYY-MM-DD): ")

    try:
        # Validate and convert start date string to datetime object
        start_dt = validate_date(start_date)
        # Validate and convert end date string to datetime object
        end_dt = validate_date(end_date)
    except ValueError:
        # Print error message if date format is invalid
        print("❌ Invalid date format. Please use YYYY-MM-DD.")
        # Continue the loop to prompt for dates again
        continue

    # Get today's date
    today = datetime.now()

    # Check if end date is in the future
    if end_dt > today:
        # Print error message if end date is in the future
        print("❌ End date cannot be in the future.")
        # Continue the loop to prompt for dates again
        continue

    # Check if start date is after end date
    if start_dt > end_dt:
        # Print error message if start date is after end date
        print("❌ Start date must be before end date.")
        # Continue the loop to prompt for dates again
        continue

    # Break the loop if dates are valid
    break

# Step 5: Choose API Based on Date Range for Temperature Data
if end_dt >= (today - timedelta(days=5)):
    # Use forecast API if the end date is recent
    URL = (
        f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}"
        f"&daily=temperature_2m_max&timezone=Australia/Perth&start_date={start_date}&end_date={end_date}"
    )
else:
    # Use archive API for older dates
    URL = (
        f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}&daily=temperature_2m_max&timezone=Australia/Perth&models=era5"
    )

# Step 6: Make API request for temperature data
response = requests.get(URL)

# Step 7: Process and display temperature results
if response.status_code == 200:
    data = response.json()

    print(f"\n✅ Max Temperatures in {CITY.capitalize()} from {start_date} to {end_date}:\n")

    for i in range(len(data["daily"]["time"])):
        date = data["daily"]["time"][i]
        max_temp = data["daily"]["temperature_2m_max"][i]
        print(f"📅 Date: {date} | 🌡️ Max Temp (°C): {max_temp:.1f}")

    # Plotting the temperature data with Matplotlib
    dates = data["daily"]["time"]
    temps = data["daily"]["temperature_2m_max"]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, temps, marker='o', linestyle='-', color='b')
    plt.xlabel("Date")
    plt.ylabel("Max Temperature (°C)")
    plt.title(f"Daily Max Temperatures in {CITY.capitalize()}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

else:
    print("\n❌ Error:", response.status_code, response.text)


# =======================
# Part 2: Compare Monthly Rain Data (Current Month vs. Same Month Last Year)
# =======================

# Get today's date to determine the current month.
now = datetime.now()
current_year = now.year
current_month = now.month

# Determine the first day of the current month.
current_month_start = datetime(current_year, current_month, 1).strftime("%Y-%m-%d")

# For the current month, if the month isn't complete, use today's date as the end date.
if now.day <= monthrange(current_year, current_month)[1]:
    current_month_end = now.strftime("%Y-%m-%d")
else:
    current_month_end = datetime(current_year, current_month, monthrange(current_year, current_month)[1]).strftime("%Y-%m-%d")

# For the same month last year (assumed complete):
last_year = current_year - 1
days_in_last_month = monthrange(last_year, current_month)[1]
last_month_start = datetime(last_year, current_month, 1).strftime("%Y-%m-%d")
last_month_end = datetime(last_year, current_month, days_in_last_month).strftime("%Y-%m-%d")

# Build URLs for precipitation data using the Archive API
URL_current = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={latitude}&longitude={longitude}"
    f"&start_date={current_month_start}&end_date={current_month_end}"
    f"&daily=precipitation_sum&timezone=Australia/Perth"
)
URL_last = (
    f"https://archive-api.open-meteo.com/v1/archive?"
    f"latitude={latitude}&longitude={longitude}"
    f"&start_date={last_month_start}&end_date={last_month_end}"
    f"&daily=precipitation_sum&timezone=Australia/Perth"
)

# Request precipitation data for current month and same month last year.
response_current = requests.get(URL_current)
response_last = requests.get(URL_last)

# Check if both requests were successful
if response_current.status_code == 200 and response_last.status_code == 200:
    data_current = response_current.json()
    data_last = response_last.json()

    # Count rainy days: consider a day "rainy" if precipitation_sum > 0.
    rainy_days_current = sum(1 for prec in data_current["daily"]["precipitation_sum"] if prec is not None and isinstance(prec, (int, float)) and float(prec) > 0)
    rainy_days_last = sum(1 for prec in data_last["daily"]["precipitation_sum"] if prec is not None and isinstance(prec, (int, float)) and float(prec) > 0)

    # Format the month name for display (e.g., "February")
    month_name = now.strftime("%B")

    # Print the comparison of rainy days
    print(f"\n🌧️ Monthly Rain Comparison for {month_name}:")
    print(f"In {month_name} {current_year}, there were {rainy_days_current} days with rain (up to {current_month_end}).")
    print(f"In {month_name} {last_year}, there were {rainy_days_last} days with rain.")
else:
    # Print error messages if data retrieval failed
    print("\n❌ Error retrieving monthly precipitation data.")
    print(f"Current month URL: {URL_current}")
    print(f"Current month status code: {response_current.status_code}, response: {response_current.text}")
    print(f"Last month URL: {URL_last}")
    print(f"Last month status code: {response_last.status_code}, response: {response_last.text}")

