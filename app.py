from flask import Flask, render_template, request, redirect, url_for, flash
import requests, sqlite3
from datetime import datetime, timedelta
from calendar import monthrange
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import dateutil.parser  # Helps parse dates from strings
import io, base64

from config import CITY_COORDINATES
from db_functions import get_weather_from_db
from api_functions import fetch_weather_from_api

app = Flask(__name__)
app.secret_key = 'secret_key'

# How many days back do we consider "near future" for forecast?
FIVE_DAYS_AGO = lambda: (datetime.now() - timedelta(days=5))

def parse_date(ds):
    return datetime.strptime(ds, "%Y-%m-%d")

def get_daily_api_chunk(city, start_dt, end_dt, use_forecast=True):
    """Make a single call to either the forecast or archive endpoint for daily max temps."""
    lat, lon = CITY_COORDINATES[city]
    start_str = start_dt.strftime('%Y-%m-%d')
    end_str   = end_dt.strftime('%Y-%m-%d')

    if use_forecast:
        url = (f"https://api.open-meteo.com/v1/forecast?"
               f"latitude={lat}&longitude={lon}"
               f"&daily=temperature_2m_max&timezone=Australia/Perth"
               f"&start_date={start_str}&end_date={end_str}")
    else:
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={lat}&longitude={lon}"
               f"&daily=temperature_2m_max&timezone=Australia/Perth"
               f"&start_date={start_str}&end_date={end_str}&models=era5")

    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

def get_daily_chunked(city, chunk_start, chunk_end):
    """
    Decide if chunk_start..chunk_end is past or near future, then call
    either 'archive' or 'forecast' API accordingly.
    If it crosses the boundary, we split into 2 sub-chunks.
    """
    today_5ago = FIVE_DAYS_AGO()

    # Entire chunk is entirely in the "past" => archive
    if chunk_end < today_5ago:
        return get_daily_api_chunk(city, chunk_start, chunk_end, use_forecast=False)

    # Entire chunk is entirely in the "near future" => forecast
    if chunk_start >= today_5ago:
        return get_daily_api_chunk(city, chunk_start, chunk_end, use_forecast=True)

    # If we reach here, the chunk straddles the boundary => split
    # e.g. chunk_start=Mar 10, chunk_end=Apr 10, today_5ago=Mar 28
    # So sub1=Mar10..Mar28(archive), sub2=Mar29..Apr10(forecast)
    sub1_end = today_5ago
    sub2_start = today_5ago + timedelta(days=1)

    data_archive = get_daily_api_chunk(city, chunk_start, sub1_end, use_forecast=False)
    data_forecast = get_daily_api_chunk(city, sub2_start, chunk_end, use_forecast=True)

    # Combine if both calls succeeded
    combined = {"daily":{"time":[],"temperature_2m_max":[]}}
    if data_archive and "daily" in data_archive and "temperature_2m_max" in data_archive["daily"]:
        combined["daily"]["time"].extend(data_archive["daily"]["time"])
        combined["daily"]["temperature_2m_max"].extend(data_archive["daily"]["temperature_2m_max"])
    if data_forecast and "daily" in data_forecast and "temperature_2m_max" in data_forecast["daily"]:
        combined["daily"]["time"].extend(data_forecast["daily"]["time"])
        combined["daily"]["temperature_2m_max"].extend(data_forecast["daily"]["temperature_2m_max"])
    return combined

def get_daily_data(city, sdate, edate):
    """Loop month-by-month, each chunk decides if we use archive or forecast or both."""
    sd, ed = parse_date(sdate), parse_date(edate)
    all_times, all_temps = [], []
    cdt = sd
    while cdt <= ed:
        y, m = cdt.year, cdt.month
        # end of this month or end_dt
        last_day = monthrange(y, m)[1]
        chunk_end = datetime(y, m, last_day)
        if chunk_end > ed: chunk_end = ed

        # fetch daily data for that chunk
        chunk_data = get_daily_chunked(city, cdt, chunk_end)
        if chunk_data and "daily" in chunk_data and "temperature_2m_max" in chunk_data["daily"]:
            all_times.extend(chunk_data["daily"]["time"])
            all_temps.extend(chunk_data["daily"]["temperature_2m_max"])

        # next chunk (move to the first day of next month)
        cdt = (cdt.replace(day=28) + timedelta(days=4)).replace(day=1)

    return {"daily": {"time": all_times, "temperature_2m_max": all_temps}}

def plot_temps(data):
    # Check that data exists and contains the "daily" key.
    if not data or "daily" not in data:
        return ""
    
    # Get the lists for times and maximum temperatures.
    t = data["daily"].get("time", [])
    v = data["daily"].get("temperature_2m_max", [])
    if not t or not v:
        return ""
    
    # Clean the data: ensure times are datetime objects and temperatures are floats.
    t_clean, v_clean = [], []
    for d, val in zip(t, v):
        if val is not None:
            # If the date is a string, parse it into a datetime object.
            if isinstance(d, str):
                try:
                    d_parsed = datetime.fromisoformat(d)
                except Exception:
                    # Fallback to a more flexible parser if the format isn't ISO.
                    d_parsed = dateutil.parser.parse(d)
                t_clean.append(d_parsed)
            else:
                # Assume it's already a datetime object.
                t_clean.append(d)
            v_clean.append(float(val))
    
    if not t_clean:
        return ""
    
    # Create a new figure for the plot.
    plt.figure(figsize=(13, 6))
    plt.plot(t_clean, v_clean, 'o-b')  # Plot points with circles ('o') connected by blue lines ('-b')
    
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
    out = base64.b64encode(buf.getvalue()).decode()
    plt.close()
    return out

@app.route('/', methods=['GET','POST'])
def index():
    if request.method=='POST':
        city = request.form.get('city','').title()
        sdate= request.form.get('start_date','')
        edate= request.form.get('end_date','')
        if city not in CITY_COORDINATES:
            flash("Invalid city")
            return redirect(url_for('index'))
        try:
            sd, ed = parse_date(sdate), parse_date(edate)
            if ed < sd:
                flash("End date < start date!")
                return redirect(url_for('index'))
        except:
            flash("Invalid date format")
            return redirect(url_for('index'))

        # 1) monthly data from DB or API
        cdt=sd; rain_map={}; t_prec=0; t_rain=0
        while cdt<=ed:
            y, m=cdt.year, cdt.month
            row=get_weather_from_db(city,y,m)
            if row: mp, rd, _=row
            else:   mp, rd, _=fetch_weather_from_api(city,y,m)
            rain_map[f"{y}-{m:02d}"]=rd if rd else 0
            if mp: t_prec+=mp
            if rd: t_rain+=rd
            cdt=(cdt.replace(day=28)+timedelta(days=4)).replace(day=1)

        # 2) daily chunked data, splitted archive/forecast
        daily = get_daily_data(city,sdate,edate)
        pimg  = plot_temps(daily)

        return render_template('results.html',
                               city=city,start_date=sdate,end_date=edate,
                               temp_data=daily,
                               plot_data=pimg,
                               rainfall_summary={
                                  "monthly_breakdown":rain_map,
                                  "total_precipitation":t_prec,
                                  "total_rainy_days":t_rain
                               })
    return render_template('index.html')

@app.route('/history', methods=['GET'])
def history():
    # Get the selected city from the query parameters, if any
    selected_city = request.args.get('city', None)
    
    # Connect to the database
    conn = sqlite3.connect("weather.db")
    c = conn.cursor()
    
    # Fetch distinct cities for the drop-down menu
    c.execute("SELECT DISTINCT city FROM weather_data")
    cities = [row[0] for row in c.fetchall()]
    
    # Prepare and execute the query based on whether a city was selected
    if selected_city:
        query = """
            SELECT city, year, month, total_precipitation, rainy_days, max_temp 
            FROM weather_data 
            WHERE city = ? 
            ORDER BY year DESC, month DESC
        """
        c.execute(query, (selected_city,))
    else:
        query = """
            SELECT city, year, month, total_precipitation, rainy_days, max_temp 
            FROM weather_data 
            ORDER BY year DESC, month DESC
        """
        c.execute(query)
    
    rows = c.fetchall()
    conn.close()
    
    # Pass the fetched data, the list of cities, and the selected city (if any) to the template
    return render_template('history.html', data=rows, cities=cities, selected_city=selected_city)


if __name__=='__main__':
    app.run(debug=True)
