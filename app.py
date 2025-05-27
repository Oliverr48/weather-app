from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import sqlite3
from datetime import datetime, timedelta
from calendar import monthrange
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dateutil.parser
import io
import base64

from config import CITY_COORDINATES
from db_functions import get_weather_from_db
from api_functions import fetch_weather_from_api

app = Flask(__name__)
app.secret_key = 'secret_key'

# How many days back do we consider "near future" for forecast?
FIVE_DAYS_AGO = lambda: (datetime.now() - timedelta(days=5))

def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format to datetime object."""
    return datetime.strptime(date_string, "%Y-%m-%d")

def get_daily_api_chunk(city, start_date, end_date, use_forecast=True):
    """Make a single call to either the forecast or archive endpoint for daily max temps."""
    latitude, longitude = CITY_COORDINATES[city]
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    if use_forecast:
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={latitude}&longitude={longitude}"
               f"&daily=temperature_2m_max&timezone=Australia/Perth"
               f"&start_date={start_str}&end_date={end_str}")
    else:
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={latitude}&longitude={longitude}"
               f"&daily=temperature_2m_max&timezone=Australia/Perth"
               f"&start_date={start_str}&end_date={end_str}&models=era5")

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_daily_chunked(city, chunk_start, chunk_end):
    """
    Decide if chunk_start..chunk_end is past or near future, then call
    either 'archive' or 'forecast' API accordingly.
    If it crosses the boundary, we split into 2 sub-chunks.
    """
    today_minus_5_days = FIVE_DAYS_AGO()

    # Entire chunk is entirely in the "past" => archive
    if chunk_end < today_minus_5_days:
        return get_daily_api_chunk(city, chunk_start, chunk_end, use_forecast=False)

    # Entire chunk is entirely in the "near future" => forecast
    if chunk_start >= today_minus_5_days:
        return get_daily_api_chunk(city, chunk_start, chunk_end, use_forecast=True)

    # If we reach here, the chunk straddles the boundary => split
    # e.g. chunk_start=Mar 10, chunk_end=Apr 10, today_minus_5_days=Mar 28
    # So sub1=Mar10..Mar28(archive), sub2=Mar29..Apr10(forecast)
    sub1_end = today_minus_5_days
    sub2_start = today_minus_5_days + timedelta(days=1)

    data_archive = get_daily_api_chunk(city, chunk_start, sub1_end, use_forecast=False)
    data_forecast = get_daily_api_chunk(city, sub2_start, chunk_end, use_forecast=True)

    # Combine if both calls succeeded
    combined = {"daily": {"time": [], "temperature_2m_max": []}}
    if data_archive and "daily" in data_archive and "temperature_2m_max" in data_archive["daily"]:
        combined["daily"]["time"].extend(data_archive["daily"]["time"])
        combined["daily"]["temperature_2m_max"].extend(data_archive["daily"]["temperature_2m_max"])
    if data_forecast and "daily" in data_forecast and "temperature_2m_max" in data_forecast["daily"]:
        combined["daily"]["time"].extend(data_forecast["daily"]["time"])
        combined["daily"]["temperature_2m_max"].extend(data_forecast["daily"]["temperature_2m_max"])
    return combined

def get_daily_data(city, start_date, end_date):
    """Loop month-by-month, each chunk decides if we use archive or forecast or both."""
    start_dt, end_dt = parse_date(start_date), parse_date(end_date)
    all_times, all_temps = [], []
    current_date = start_dt
    
    while current_date <= end_dt:
        year, month = current_date.year, current_date.month
        # end of this month or end_dt
        last_day = monthrange(year, month)[1]
        chunk_end = datetime(year, month, last_day)
        if chunk_end > end_dt:
            chunk_end = end_dt

        # fetch daily data for that chunk
        chunk_data = get_daily_chunked(city, current_date, chunk_end)
        if chunk_data and "daily" in chunk_data and "temperature_2m_max" in chunk_data["daily"]:
            all_times.extend(chunk_data["daily"]["time"])
            all_temps.extend(chunk_data["daily"]["temperature_2m_max"])

        # next chunk (move to the first day of next month)
        current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

    return {"daily": {"time": all_times, "temperature_2m_max": all_temps}}

def plot_temps(data):
    """Generate a temperature plot and return it as base64 encoded image."""
    # Check that data exists and contains the "daily" key.
    if not data or "daily" not in data:
        return ""
    
    # Get the lists for times and maximum temperatures.
    times = data["daily"].get("time", [])
    values = data["daily"].get("temperature_2m_max", [])
    if not times or not values:
        return ""
    
    # Clean the data: ensure times are datetime objects and temperatures are floats.
    times_clean, values_clean = [], []
    for date, val in zip(times, values):
        if val is not None:
            # If the date is a string, parse it into a datetime object.
            if isinstance(date, str):
                try:
                    date_parsed = datetime.fromisoformat(date)
                except Exception:
                    # Fallback to a more flexible parser if the format isn't ISO.
                    date_parsed = dateutil.parser.parse(date)
                times_clean.append(date_parsed)
            else:
                # Assume it's already a datetime object.
                times_clean.append(date)
            values_clean.append(float(val))
    
    if not times_clean:
        return ""
    
    # Create a new figure for the plot.
    plt.figure(figsize=(13, 6))
    plt.plot(times_clean, values_clean, 'o-b')  # Plot points with circles ('o') connected by blue lines ('-b')
    
    # Set up automatic date locators and formatters so the x-axis shows proper dates.
    locator = mdates.AutoDateLocator(minticks=8, maxticks=16)
    formatter = mdates.ConciseDateFormatter(locator)
    ax = plt.gca()  # Get current axes
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)
    
    # Rotate x-axis labels for better readability.
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot to an in-memory bytes buffer as a PNG image.
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode the image in base64 so it can be easily transmitted or embedded.
    output = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    return output

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route for weather data input and processing."""
    if request.method == 'POST':
        city = request.form.get('city', '').title()
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        
        if city not in CITY_COORDINATES:
            flash("Invalid city")
            return redirect(url_for('index'))
        
        try:
            start_dt, end_dt = parse_date(start_date), parse_date(end_date)
            if end_dt < start_dt:
                flash("End date < start date!")
                return redirect(url_for('index'))
        except:
            flash("Invalid date format")
            return redirect(url_for('index'))

        # 1) monthly data from DB or API
        current_date = start_dt
        rain_map = {}
        total_precipitation = 0
        total_rain_days = 0
        
        while current_date <= end_dt:
            year, month = current_date.year, current_date.month
            row = get_weather_from_db(city, year, month)
            if row:
                monthly_precip, rainy_days, _ = row
            else:
                monthly_precip, rainy_days, _ = fetch_weather_from_api(city, year, month)
            
            rain_map[f"{year}-{month:02d}"] = rainy_days if rainy_days else 0
            if monthly_precip:
                total_precipitation += monthly_precip
            if rainy_days:
                total_rain_days += rainy_days
            current_date = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)

        # 2) daily chunked data, splitted archive/forecast
        daily_data = get_daily_data(city, start_date, end_date)
        plot_image = plot_temps(daily_data)

        return render_template('results.html',
                               city=city, start_date=start_date, end_date=end_date,
                               temp_data=daily_data,
                               plot_data=plot_image,
                               rainfall_summary={
                                   "monthly_breakdown": rain_map,
                                   "total_precipitation": total_precipitation,
                                   "total_rainy_days": total_rain_days
                               })
    return render_template('index.html')

@app.route('/history', methods=['GET'])
def history():
    """Display historical weather data from the database."""
    # Get the selected city from the query parameters, if any
    selected_city = request.args.get('city', None)
    
    # Connect to the database
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()
    
    # Fetch distinct cities for the drop-down menu
    cursor.execute("SELECT DISTINCT city FROM weather_data")
    cities = [row[0] for row in cursor.fetchall()]
    
    # Prepare and execute the query based on whether a city was selected
    if selected_city:
        query = """
            SELECT city, year, month, total_precipitation, rainy_days, max_temp 
            FROM weather_data 
            WHERE city = ? 
            ORDER BY year DESC, month DESC
        """
        cursor.execute(query, (selected_city,))
    else:
        query = """
            SELECT city, year, month, total_precipitation, rainy_days, max_temp 
            FROM weather_data 
            ORDER BY year DESC, month DESC
        """
        cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()
    
    # Pass the fetched data, the list of cities, and the selected city (if any) to the template
    return render_template('history.html', data=rows, cities=cities, selected_city=selected_city)

if __name__ == '__main__':
    app.run(debug=True)
