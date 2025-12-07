# dashboard.py - Enhanced with Weather Forecast Feature

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import requests
try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None
from config import (
    DATA_ARCHIVE_FILE,
    CROP_PROFILES,
    DROUGHT_THRESHOLD,
    WET_THRESHOLD,
    EXTREME_TEMP_HIGH,
    EXTREME_TEMP_LOW,
    API_KEY,
    AGRICULTURAL_ZONES,
    API_TIMEOUT,
    API_TIMEOUT,
    FORECAST_API_URL,
    SUPABASE_URL,
    SUPABASE_KEY,
)

# Set page configuration
st.set_page_config(
    layout="wide",
    page_title="Abia State ADSS",
    page_icon="🌾",
    initial_sidebar_state="expanded",
)

# Premium Modern UI Styling (Dark Mode)
st.markdown(
    """
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

        /* Main Container */
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
            font-family: 'Inter', sans-serif;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }

        /* Titles */
        h1, h2, h3 {
            color: #e6edf3 !important;
            font-weight: 700;
        }
        
        .main-header {
            font-size: 2.2rem;
            background: linear-gradient(90deg, #4CAF50 0%, #81C784 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
            padding-bottom: 1rem;
        }

        /* Cards / Metrics */
        div[data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #66bb6a;
        }
        
        div[data-testid="metric-container"] {
            background-color: #1f242d;
            border: 1px solid #30363d;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: transform 0.2s;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.4);
            border-color: #66bb6a;
        }
        
        div[data-testid="stMetricLabel"] {
            color: #b0b8c4;
        }

        /* Custom Cards */
        .forecast-card {
            background: #1f242d;
            padding: 1.25rem;
            border-radius: 12px;
            border: 1px solid #30363d;
            margin-bottom: 0.75rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            color: #e6edf3;
            transition: all 0.2s ease;
        }
        .forecast-card:hover {
            border-color: #66bb6a;
            transform: translateX(4px);
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: transparent;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #1f242d;
            border-radius: 8px 8px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
            border: 1px solid #30363d;
            border-bottom: none;
            color: #b0b8c4;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #2E7D32;
            color: white;
            border: none;
        }

        /* Hourly Table */
        .hourly-table-container {
            display: grid;
            grid-template-columns: repeat(8, 1fr);
            text-align: center;
            background: #1f242d;
            padding: 1rem 0;
            border-radius: 8px;
            margin-top: 0.5rem;
            border: 1px solid #30363d;
        }
        .hourly-table-cell {
            padding: 0.25rem;
            font-size: 0.85rem;
            color: #e6edf3;
            font-weight: 500;
        }
        
        /* Remove default Streamlit chrome but keep header for sidebar toggle if needed */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* header {visibility: hidden;}  <-- Commented out to allow sidebar toggle access if needed, 
           but we are moving controls to main page anyway. */
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Utility Functions ---

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_hourly_forecast(zone_name):
    """Fetch hourly forecast for next 48 hours using OpenWeatherMap API."""
    try:
        coords = AGRICULTURAL_ZONES[zone_name]
        url = FORECAST_API_URL # Use the URL from config.py
        
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": API_KEY,
            "units": "metric",
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        forecast_list = []
        # Get first 8 entries for 24 hours (3-hour intervals) or more for 48 hours
        for item in data["list"][:16]:  
            forecast_list.append({
                "datetime": datetime.fromtimestamp(item["dt"]),
                "temp": item["main"]["temp"],
                "feels_like": item["main"]["feels_like"],
                "humidity": item["main"]["humidity"],
                "pressure": item["main"]["pressure"],
                "weather": item["weather"][0]["main"],
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "clouds": item["clouds"]["all"],
                "wind_speed": item["wind"]["speed"],
                "rain_3h": item.get("rain", {}).get("3h", 0.0),
                "pop": item.get("pop", 0) * 100,  # Probability of precipitation
            })
        
        return pd.DataFrame(forecast_list)
    
    except Exception as e:
        st.error(f"Error fetching hourly forecast: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_daily_forecast(zone_name):
    """Fetch 5-day daily forecast aggregated from the 3-hour forecast API."""
    try:
        coords = AGRICULTURAL_ZONES[zone_name]
        url = FORECAST_API_URL # Use the URL from config.py
        
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": API_KEY,
            "units": "metric",
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        # Aggregate by day
        daily_data = {}
        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            date_key = dt.date()
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "temps": [],
                    "humidity": [],
                    "weather": [],
                    "rain": 0,
                    "wind_speed": [],
                    "clouds": [],
                }
            
            daily_data[date_key]["temps"].append(item["main"]["temp"])
            daily_data[date_key]["humidity"].append(item["main"]["humidity"])
            daily_data[date_key]["weather"].append(item["weather"][0]["main"])
            daily_data[date_key]["rain"] += item.get("rain", {}).get("3h", 0.0)
            daily_data[date_key]["wind_speed"].append(item["wind"]["speed"])
            daily_data[date_key]["clouds"].append(item["clouds"]["all"])
        
        # Create daily forecast dataframe
        forecast_list = []
        for date_key, values in sorted(daily_data.items()):
            # Find the most frequent weather condition for the day
            most_frequent_weather = max(set(values["weather"]), key=values["weather"].count)
            # Find the most relevant description (can be complex, but sticking to main weather for simplicity)
            
            forecast_list.append({
                "date": date_key,
                "temp_max": max(values["temps"]),
                "temp_min": min(values["temps"]),
                "humidity": np.mean(values["humidity"]),
                "weather": most_frequent_weather,
                "total_rain": values["rain"],
                "wind_speed": np.mean(values["wind_speed"]),
                "clouds": np.mean(values["clouds"]),
            })
        
        return pd.DataFrame(forecast_list)
    
    except Exception as e:
        st.error(f"Error fetching daily forecast: {e}")
        return pd.DataFrame()


def get_weather_emoji(weather_condition):
    """Return emoji for weather condition."""
    weather_emojis = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧️",
        "Drizzle": "🌦️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
        "Mist": "🌫️",
        "Fog": "🌫️",
        "Haze": "🌫️",
        "Smoke": "🌫️",
        "Dust": "💨",
        "Sand": "💨",
        "Ash": "💨",
        "Squall": "🌬️",
        "Tornado": "🌪️",
    }
    return weather_emojis.get(weather_condition, "🌤️")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Loads, cleans, and preprocesses the archived weather data."""
    # Try Supabase first
    if SUPABASE_URL and SUPABASE_KEY and create_client:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table("weather_data").select("*").execute()
            
            if response.data:
                df = pd.DataFrame(response.data)
                
                # Column mapping (Supabase snake_case -> Dashboard Title Case)
                # Map only if necessary. If user created table with Title Case, this might fail or be redundant.
                # Assuming standard Supabase lowercase, we map common columns.
                column_map = {
                    "timestamp": "Timestamp",
                    "zone": "Zone",
                    "t_current": "T_current",
                    "t_min": "T_min",
                    "t_max": "T_max",
                    "feels_like": "Feels_Like",
                    "humidity": "Humidity",
                    "pressure": "Pressure",
                    "wind_speed": "Wind_Speed",
                    "wind_direction": "Wind_Direction",
                    "cloudiness": "Cloudiness",
                    "precipitation_1h": "Precipitation_1h",
                    "precipitation_3h": "Precipitation_3h",
                    "weather_condition": "Weather_Condition",
                    "weather_description": "Weather_Description",
                    "visibility": "Visibility"
                }
                
                # Rename columns that match
                df.rename(columns=column_map, inplace=True)
                
                # If specific columns like T_current are missing (maybe they are already Title Case in DB), check and keep original
                
                # Core cleaning
                df["Timestamp"] = pd.to_datetime(df["Timestamp"])
                df.set_index("Timestamp", inplace=True)
                
                # Ensure numeric columns
                numeric_cols = [
                    "T_current", "T_min", "T_max", "Humidity", 
                    "Precipitation_1h", "Precipitation_3h"
                ]
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                        
                df.dropna(subset=["T_min", "T_max"], inplace=True)
                df.sort_index(inplace=True)
                
                # Add source indicator for debugging (optional, can remove)
                # st.toast("Loaded data from Supabase DB") 
                
                return df
                
        except Exception as e:
            st.warning(f"⚠️ Could not load from Supabase ({e}). Falling back to local archive.")
    
    # Fallback to local CSV
    if not os.path.exists(DATA_ARCHIVE_FILE):
        st.error(
            f"⚠️ Data archive '{DATA_ARCHIVE_FILE}' not found. "
            "Please run data_collector.py first to generate data."
        )
        return pd.DataFrame()

    try:
        df = pd.read_csv(DATA_ARCHIVE_FILE)

        # Core cleaning
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        df.set_index("Timestamp", inplace=True)

        # Ensure numeric columns
        numeric_cols = [
            "T_current",
            "T_min",
            "T_max",
            "Humidity",
            "Precipitation_1h",
            "Precipitation_3h",
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop rows with missing critical data
        df.dropna(subset=["T_min", "T_max"], inplace=True)

        # Sort by timestamp
        df.sort_index(inplace=True)

        return df

    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()


def calculate_daily_aggregates(df_zone):
    """Calculate daily aggregates from hourly data."""
    if df_zone.empty:
        return pd.DataFrame()

    # Resample to daily
    daily = df_zone.resample("D").agg(
        {
            "T_min": "min",
            "T_max": "max",
            "T_current": "mean",
            "Humidity": "mean",
            "Precipitation_1h": "sum",
        }
    )

    daily.rename(columns={"Precipitation_1h": "Daily_Precipitation"}, inplace=True)
    daily["T_avg"] = (daily["T_max"] + daily["T_min"]) / 2

    return daily.dropna()


def calculate_gdd(df_zone, T_base):
    """Calculates Daily and Cumulative GDD for a given T_base."""
    daily = calculate_daily_aggregates(df_zone)

    if daily.empty:
        return pd.DataFrame()

    # Apply GDD formula: max(0, T_avg - T_base)
    daily["Daily_GDD"] = np.maximum(0, daily["T_avg"] - T_base)
    daily["Cumulative_GDD"] = daily["Daily_GDD"].cumsum()

    return daily


def identify_wet_dry_periods(df_zone, window=7):
    """Calculates rolling rainfall and assigns risk flags."""
    daily = calculate_daily_aggregates(df_zone)

    if daily.empty or "Daily_Precipitation" not in daily.columns:
        return pd.DataFrame()

    df_risk = daily[["Daily_Precipitation"]].copy()
    df_risk.rename(columns={"Daily_Precipitation": "Daily_Rain"}, inplace=True)

    # Calculate rolling sum
    df_risk["Rain_7D_Sum"] = df_risk["Daily_Rain"].rolling(window=window, min_periods=1).sum()

    # Assign risk flags
    def set_risk_flag(rain_sum):
        if rain_sum <= DROUGHT_THRESHOLD:
            return "Drought Risk"
        elif rain_sum >= WET_THRESHOLD:
            return "Waterlogging Risk"
        else:
            return "Normal"

    df_risk["Risk_Flag"] = df_risk["Rain_7D_Sum"].apply(set_risk_flag)

    return df_risk


def suggest_crops(df_zone):
    """Compares zone climate profile to crop requirements."""
    daily = calculate_daily_aggregates(df_zone)

    if daily.empty:
        return pd.DataFrame()

    # Calculate climate metrics
    mean_tmin = daily["T_min"].mean()
    mean_tmax = daily["T_max"].mean()

    # Estimate annual rainfall (sum of last 365 days)
    last_year_rain = daily["Daily_Precipitation"].tail(365).sum()

    suggestions = []

    for crop, reqs in CROP_PROFILES.items():
        reasons = []
        suitability_score = 0

        # Temperature check
        if mean_tmin >= reqs["T_base"]:
            reasons.append(f"✓ Meets T_base ({reqs['T_base']:.1f}°C)")
            suitability_score += 1

        # Optimal temperature range
        if (
            "T_optimal_min" in reqs
            and reqs["T_optimal_min"] <= mean_tmax <= reqs["T_optimal_max"]
        ):
            reasons.append("✓ Within optimal temperature range")
            suitability_score += 1

        # Rainfall check
        if reqs["Rain_Annual_Min"] <= last_year_rain <= reqs["Rain_Annual_Max"]:
            reasons.append("✓ Rainfall within ideal range")
            suitability_score += 1

        # Determine suitability
        if suitability_score >= 3:
            suitability = "🟢 Highly Suitable"
        elif suitability_score == 2:
            suitability = "🟡 Moderately Suitable"
        else:
            suitability = "🔴 Not Suitable"

        suggestions.append(
            {
                "Crop": crop,
                "Suitability": suitability,
                "Mean T_min": f"{mean_tmin:.1f}°C",
                "Mean T_max": f"{mean_tmax:.1f}°C",
                "Annual Rain": f"{last_year_rain:.0f} mm",
                "Notes": " | ".join(reasons) if reasons else "Does not meet requirements",
            }
        )

    return pd.DataFrame(suggestions)


def calculate_statistics(df_zone):
    """Calculate comprehensive statistics for the zone."""
    daily = calculate_daily_aggregates(df_zone)

    if daily.empty:
        return {}

    stats = {
        "avg_temp": daily["T_avg"].mean(),
        "max_temp": daily["T_max"].max(),
        "min_temp": daily["T_min"].min(),
        "avg_humidity": daily["Humidity"].mean(),
        "total_rain_30d": daily["Daily_Precipitation"].tail(30).sum(),
        "total_rain_90d": daily["Daily_Precipitation"].tail(90).sum(),
        "avg_daily_rain": daily["Daily_Precipitation"].mean(),
    }
    return stats


def calculate_annual_metrics(df_zone):
    """Calculate annual rainfall and average temperature."""
    daily = calculate_daily_aggregates(df_zone)
    if daily.empty:
        return pd.DataFrame()
        
    annual = daily.resample("Y").agg(
        {
            "Daily_Precipitation": "sum",
            "T_avg": "mean"
        }
    )
    annual.index = annual.index.year
    return annual


def calculate_planting_onset(df_zone):
    """
    Identify potential planting onset date for each year.
    Heuristic: First day after March 1st with > 20mm rain in 3 days.
    """
    daily = calculate_daily_aggregates(df_zone)
    if daily.empty:
        return pd.DataFrame()
        
    onsets = []
    years = daily.index.year.unique()
    
    for year in years:
        # Filter for planting window (March - June)
        start_date = pd.Timestamp(f"{year}-03-01")
        if daily.index.tz is not None:
            start_date = start_date.tz_localize(daily.index.tz)
            
        mask = (daily.index >= start_date) & (daily.index.year == year)
        season_data = daily[mask].copy()
        
        # Rolling 3-day rainfall
        season_data["Rain_3D"] = season_data["Daily_Precipitation"].rolling(3).sum()
        
        # Find first occurrence > 20mm
        onset_dates = season_data[season_data["Rain_3D"] >= 20].index
        
        if not onset_dates.empty:
            onset = onset_dates[0]
            # Calculate Day of Year for plotting
            day_of_year = onset.dayofyear
            onsets.append({"Year": year, "Onset_Date": onset, "Day_Of_Year": day_of_year})
            
    return pd.DataFrame(onsets)


def calculate_drought_frequency_yearly(df_zone):
    """Count number of drought days per year."""
    df_risk = identify_wet_dry_periods(df_zone)
    if df_risk.empty:
        return pd.DataFrame()
        
    # Filter for drought days
    drought_days = df_risk[df_risk["Risk_Flag"] == "Drought Risk"]
    
    # Group by year
    yearly_droughts = drought_days.resample("Y").size()
    yearly_droughts.index = yearly_droughts.index.year
    
    return pd.DataFrame({"Drought_Days": yearly_droughts})


def calculate_historical_seasonality(df_zone):
    """
    Calculate historical daily averages (Baseline) excluding the current year.
    Returns DataFrame indexed by DayOfYear (1-366).
    """
    if df_zone.empty:
        return pd.DataFrame()
        
    # Exclude current year for baseline
    current_year = datetime.now().year
    df_hist = df_zone[df_zone.index.year < current_year].copy()
    
    if df_hist.empty:
        # Fallback to all data if no previous years
        df_hist = df_zone.copy()
        
    daily = calculate_daily_aggregates(df_hist)
    daily["DayOfYear"] = daily.index.dayofyear
    
    seasonality = daily.groupby("DayOfYear").agg({
        "T_max": "mean",
        "T_min": "mean",
        "T_avg": "mean",
        "Daily_Precipitation": "mean"
    })
    
    # Smooth the curves slightly for better baseline visualization
    seasonality = seasonality.rolling(window=7, center=True, min_periods=1).mean()
    
    return seasonality


# --- Main Dashboard ---

# Load data
df_raw = load_data()

if df_raw.empty:
    st.stop()

# Header
st.markdown('<h1 class="main-header">🌾 Abia State Agricultural Decision Support System</h1>', unsafe_allow_html=True)
st.markdown("**Real-time weather analytics and crop management advisory for agricultural zones**")
st.markdown("---")

# --- Navigation & Controls (Main Top Bar) ---
# Create a container for controls to make them prominent
st.markdown("""<div style="background-color: #161b22; padding: 1rem; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 2rem;">""", unsafe_allow_html=True)
col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 1])

with col_nav1:
    st.markdown("### 📍 Location & Timeframe")
    
with col_nav2:
    unique_zones = sorted(df_raw["Zone"].unique())
    # Default to first one or preserve state if possible (Streamlit handles state auto)
    selected_zone = st.selectbox("Select Agricultural Zone:", unique_zones)

with col_nav3:
    date_range = st.selectbox(
        "Select Timeframe:",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Data"],
        index=2,
    )
st.markdown("</div>", unsafe_allow_html=True)

# Filter data based on selection
df_zone = df_raw[df_raw["Zone"] == selected_zone].copy()

if date_range == "Last 7 Days":
    df_zone = df_zone.last("7D")
elif date_range == "Last 30 Days":
    df_zone = df_zone.last("30D")
elif date_range == "Last 90 Days":
    df_zone = df_zone.last("90D")

# Removed sidebar info as it's cleaner without it, or move to bottom
# st.sidebar.info(...) -> Removed

# Tabs
# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "📊 Overview & Trends",
        "🔮 Weather Forecast",
        "📜 Historical Trends",
        "💧 Risk Analysis",
        "🌱 GDD Tracking",
        "🗓️ Crop Planning",
        "📁 Data Archive",
    ]
)

# --- TAB 1: Overview & Trends (Logic is complete) ---
with tab1:
    st.header(f"📊 Weather Overview for {selected_zone}")

    if df_zone.empty:
        st.warning("No data available for the selected zone and timeframe.")
    else:
        # Latest conditions
        latest = df_zone.iloc[-1]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🌡️ Current Temperature",
                f"{latest['T_current']:.1f} °C",
                delta=f"{latest['T_current'] - df_zone['T_current'].mean():.1f}°C vs avg",
            )

        with col2:
            st.metric("💧 Humidity", f"{latest['Humidity']:.0f}%")

        with col3:
            rain_value = latest.get("Precipitation_1h", 0.0)
            st.metric("🌧️ Last Hour Rain", f"{rain_value:.1f} mm")

        with col4:
            if "Wind_Speed" in latest:
                st.metric("💨 Wind Speed", f"{latest['Wind_Speed']:.1f} m/s")

        st.markdown("---")

        # Statistics
        stats = calculate_statistics(df_zone)

        if stats:
            st.subheader("📈 Statistical Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Temperature Statistics**")
                st.write(f"Average: {stats['avg_temp']:.1f}°C")
                st.write(f"Maximum: {stats['max_temp']:.1f}°C")
                st.write(f"Minimum: {stats['min_temp']:.1f}°C")

            with col2:
                st.markdown("**Rainfall Summary**")
                st.write(f"Last 30 days: {stats['total_rain_30d']:.1f} mm")
                st.write(f"Last 90 days: {stats['total_rain_90d']:.1f} mm")
                st.write(f"Daily average: {stats['avg_daily_rain']:.1f} mm")

            with col3:
                st.markdown("**Other Metrics**")
                st.write(f"Avg Humidity: {stats['avg_humidity']:.1f}%")

        # Temperature trend
        st.subheader("🌡️ Temperature Trends")

        fig_temp = go.Figure()
        fig_temp.add_trace(
            go.Scatter(
                x=df_zone.index,
                y=df_zone["T_max"],
                name="T_max",
                line=dict(color="red"),
                hovertemplate="Max T: %{y:.1f}°C<extra></extra>",
            )
        )
        fig_temp.add_trace(
            go.Scatter(
                x=df_zone.index,
                y=df_zone["T_current"],
                name="T_current",
                line=dict(color="orange"),
                hovertemplate="Current T: %{y:.1f}°C<extra></extra>",
            )
        )
        fig_temp.add_trace(
            go.Scatter(
                x=df_zone.index,
                y=df_zone["T_min"],
                name="T_min",
                line=dict(color="blue"),
                hovertemplate="Min T: %{y:.1f}°C<extra></extra>",
            )
        )

        fig_temp.update_layout(
            title="Temperature Variations",
            xaxis_title="Date",
            yaxis_title="Temperature (°C)",
            hovermode="x unified",
        )

        st.plotly_chart(fig_temp, use_container_width=True)

        # Wind & Pressure Analysis
        st.subheader("🌬️ Wind & Atmosphere Analysis")
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            # Wind Rose (Polar Scatter of recent 24h)
            st.markdown("**Wind Direction (Last 24h)**")
            
            # Filter last 24h
            df_wind = df_zone.tail(24)
            
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Scatterpolar(
                r=df_wind["Wind_Speed"],
                theta=df_wind["Wind_Direction"],
                mode='markers',
                marker=dict(
                    color=df_wind["Wind_Speed"],
                    colorscale='Viridis',
                    size=10,
                    showscale=True,
                    colorbar=dict(title="Speed (m/s)")
                ),
                name='Wind'
            ))
            
            fig_wind.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, df_wind["Wind_Speed"].max() + 2]),
                    angularaxis=dict(direction="clockwise")
                ),
                showlegend=False,
                height=350,
                margin=dict(l=40, r=40, t=20, b=20)
            )
            st.plotly_chart(fig_wind, use_container_width=True)

        with col_w2:
            # Pressure Trend
            st.markdown("**Atmospheric Pressure Trend**")
            fig_press = px.line(df_zone.tail(24), x=df_zone.tail(24).index, y="Pressure", markers=True)
            fig_press.update_traces(line_color="#4FC3F7")
            fig_press.update_layout(height=350, xaxis_title="Time", yaxis_title="hPa")
            st.plotly_chart(fig_press, use_container_width=True)

# --- TAB 2: Weather Forecast (Enhanced to match screenshot) ---
with tab2:
    st.header(f"🔮 Weather Forecast for {selected_zone}")
    
    # Fetch forecast data
    with st.spinner("Fetching forecast data..."):
        df_hourly = fetch_hourly_forecast(selected_zone)
        df_daily = fetch_daily_forecast(selected_zone).head(8) # Limiting to 8 for a clear display
    
    if not df_hourly.empty or not df_daily.empty:
        # Create two columns for hourly and daily forecast
        col_left, col_right = st.columns([1, 1])
        
        # --- Hourly Forecast ---
        with col_left:
            st.subheader("⏰ Hourly Forecast (Next 48 Hours)")
            
            if not df_hourly.empty:
                # Temperature line chart (already defined above)
                fig_hourly = go.Figure()
                fig_hourly.add_trace(
                    go.Scatter(
                        x=df_hourly["datetime"],
                        y=df_hourly["temp"],
                        name="Temperature",
                        line=dict(color="#FF6B6B", width=3),
                        mode="lines+markers",
                        hovertemplate="Temp: %{y:.1f}°C<extra>%{x|%a %I:%M%p}</extra>",
                    )
                )
                
                # Add precipitation probability as bars
                fig_hourly.add_trace(
                    go.Bar(
                        x=df_hourly["datetime"],
                        y=df_hourly["pop"],
                        name="Precip. Probability (%)",
                        yaxis="y2",
                        marker=dict(color="#4ECDC4", opacity=0.3),
                        hovertemplate="PoP: %{y:.0f}%<extra></extra>",
                    )
                )
                
                fig_hourly.update_layout(
                    title="Temperature & Precipitation Probability",
                    xaxis_title="Time",
                    yaxis_title="Temperature (°C)",
                    yaxis2=dict(
                        title="Precipitation Probability (%)",
                        overlaying="y",
                        side="right",
                        range=[0, 100],
                    ),
                    hovermode="x unified",
                    height=400,
                )
                
                st.plotly_chart(fig_hourly, use_container_width=True)
                
                # --- Implementation of the detailed data rows (as seen in screenshot) ---
                hourly_display = df_hourly.head(8).copy() # Showing next 24 hours (8 intervals)
                
                # Create the HTML structure for the multi-row table
                time_row = "".join([f'<div class="hourly-table-cell"><strong>{dt.strftime("%I%p")}</strong></div>' for dt in hourly_display["datetime"]])
                temp_row = "".join([f'<div class="hourly-table-cell">{temp:.1f}°</div>' for temp in hourly_display["temp"]])
                pop_row = "".join([f'<div class="hourly-table-cell" style="color:#2E7D32;">{pop:.0f}%</div>' for pop in hourly_display["pop"]])
                weather_row = "".join([f'<div class="hourly-table-cell" title="{desc}">{desc.replace(" ", "<br>")}</div>' for desc, desc_full in zip(hourly_display["description"].str.split().str[0], hourly_display["description"])])
                wind_row = "".join([f'<div class="hourly-table-cell">{wind:.1f}m/s</div>' for wind in hourly_display["wind_speed"]])
                
                st.markdown("---")
                st.markdown(f"**Hourly Details** (Next 24 Hours)")
                
                st.markdown(f'<div class="hourly-table-container">{time_row}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="hourly-table-container" style="color: #FF6B6B;">{temp_row}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="hourly-table-container">{pop_row}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="hourly-table-container" style="font-size: 0.75rem;">{weather_row}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="hourly-table-container">{wind_row}</div>', unsafe_allow_html=True)


        # --- Daily Forecast ---
        with col_right:
            st.subheader("📅 Daily Forecast (5-Day)")
            
            if not df_daily.empty:
                # Display daily forecast cards
                for idx, row in df_daily.iterrows():
                    date_str = row["date"].strftime("%a, %b %d")
                    emoji = get_weather_emoji(row["weather"])
                    weather_desc = row["weather"].replace(" ", " ").title() # Clean up weather name
                    
                    # Custom HTML for a cleaner daily card matching the screenshot style
                    st.markdown(f"""
                        <div class="forecast-card">
                            <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 0.5rem;">
                                <strong style="width: 30%;">{date_str}</strong>
                                <div style="font-size: 1.5rem; width: 15%; text-align: center;">{emoji}</div>
                                <strong style="width: 35%; text-align: right;">{row["temp_max"]:.0f}° / {row["temp_min"]:.0f}°C</strong>
                                <div style="color: #666; width: 20%; text-align: right; font-size: 0.9rem;">{weather_desc}</div>
                            </div>
                            <div style="font-size: 0.8rem; color: #999; text-align: right;">
                                Rain: {row["total_rain"]:.1f} mm | Wind: {row["wind_speed"]:.1f} m/s
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("---")
                
                # Daily temperature range chart (already defined above)
                st.markdown("**Temperature Range Forecast**")
                fig_daily = go.Figure()
                
                fig_daily.add_trace(
                    go.Scatter(
                        x=df_daily["date"],
                        y=df_daily["temp_max"],
                        name="Max Temp",
                        line=dict(color="#FF6B6B"),
                        mode="lines+markers",
                    )
                )
                
                fig_daily.add_trace(
                    go.Scatter(
                        x=df_daily["date"],
                        y=df_daily["temp_min"],
                        name="Min Temp",
                        line=dict(color="#4ECDC4"),
                        mode="lines+markers",
                        fill="tonexty",
                        fillcolor="rgba(78, 205, 196, 0.2)",
                    )
                )
                
                fig_daily.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Temperature (°C)",
                    hovermode="x unified",
                    height=300,
                )
                
                st.plotly_chart(fig_daily, use_container_width=True)
        
    else:
        st.error("Unable to fetch forecast data. Please check your API key and internet connection.")

# --- TAB 4: Risk Analysis ---
with tab4:
    st.header(f"💧 Risk Analysis for {selected_zone}")

    df_risk = identify_wet_dry_periods(df_zone)

    if df_risk.empty:
        st.warning("⚠️ Insufficient data for risk analysis.")
    else:
        latest_risk = df_risk.iloc[-1]

        # Risk alert
        if latest_risk["Risk_Flag"] == "Drought Risk":
            st.error(
                f"🚨 **DROUGHT ALERT**: 7-day rainfall is {latest_risk['Rain_7D_Sum']:.1f} mm "
                f"(threshold: ≤ {DROUGHT_THRESHOLD} mm). Consider irrigation measures."
            )
        elif latest_risk["Risk_Flag"] == "Waterlogging Risk":
            st.error(
                f"⚠️ **WATERLOGGING ALERT**: 7-day rainfall is {latest_risk['Rain_7D_Sum']:.1f} mm "
                f"(threshold: ≥ {WET_THRESHOLD} mm). Monitor for crop disease."
            )
        else:
            st.success(
                f"✅ **NORMAL CONDITIONS**: 7-day rainfall is {latest_risk['Rain_7D_Sum']:.1f} mm. "
                "No immediate risk detected."
            )

        # Visualization
        st.subheader("📊 Rainfall and Risk Trends")

        fig_rain = px.bar(
            df_risk.tail(90).reset_index(),
            x="Timestamp",
            y="Daily_Rain",
            color="Risk_Flag",
            color_discrete_map={
                "Drought Risk": "#d32f2f",
                "Waterlogging Risk": "#1976d2",
                "Normal": "#388e3c",
            },
            title="Daily Rainfall with Risk Classification (Last 90 Days)",
        )

        fig_rain.update_layout(xaxis_title="Date", yaxis_title="Rainfall (mm)")
        st.plotly_chart(fig_rain, use_container_width=True)

        # Gauge Chart for Current Status
        st.subheader("⏱️ Current Risk Monitor")
        
        # Determine gauge color based on risk
        gauge_color = "#4caf50" # Green
        if latest_risk['Rain_7D_Sum'] < DROUGHT_THRESHOLD:
            gauge_color = "#ef5350" # Red
        elif latest_risk['Rain_7D_Sum'] > WET_THRESHOLD:
            gauge_color = "#42a5f5" # Blue
            
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = latest_risk['Rain_7D_Sum'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "7-Day Cumulative Rainfall (mm)", 'font': {'size': 20}},
            delta = {'reference': DROUGHT_THRESHOLD, 'increasing': {'color': "blue"}, 'decreasing': {'color': "red"}},
            gauge = {
                'axis': {'range': [None, 200], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': gauge_color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "#333",
                'steps': [
                    {'range': [0, DROUGHT_THRESHOLD], 'color': 'rgba(239, 83, 80, 0.3)'},
                    {'range': [DROUGHT_THRESHOLD, WET_THRESHOLD], 'color': 'rgba(102, 187, 106, 0.3)'},
                    {'range': [WET_THRESHOLD, 200], 'color': 'rgba(66, 165, 245, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': DROUGHT_THRESHOLD
                }
            }
        ))
        
        fig_gauge.update_layout(height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Rolling sum chart
        fig_rolling = px.line(
            df_risk.tail(90).reset_index(),
            x="Timestamp",
            y="Rain_7D_Sum",
            title="7-Day Rolling Rainfall Sum",
        )

        fig_rolling.add_hline(
            y=DROUGHT_THRESHOLD,
            line_dash="dash",
            line_color="red",
            annotation_text="Drought Threshold",
        )
        fig_rolling.add_hline(
            y=WET_THRESHOLD,
            line_dash="dash",
            line_color="blue",
            annotation_text="Waterlogging Threshold",
        )

        st.plotly_chart(fig_rolling, use_container_width=True)

# --- TAB 3: Historical Trends ---
with tab3:
    st.header(f"📜 Historical Climate Trends for {selected_zone}")
    st.info("Analysis based on available historical data (2020-2025).")
    
    # Use full dataset for historical trends, ignoring the sidebar date filter
    df_history = df_raw[df_raw["Zone"] == selected_zone].copy()
    
    if df_history.empty:
        st.warning("Insufficient data for trend analysis.")
    else:
        # 1. Annual Rainfall Comparison
        st.subheader("🌧️ Annual Rainfall Comparison")
        annual_metrics = calculate_annual_metrics(df_history)
        
        if not annual_metrics.empty:
            fig_annual_rain = px.bar(
                annual_metrics,
                x=annual_metrics.index,
                y="Daily_Precipitation",
                title="Total Annual Rainfall (mm)",
                labels={"index": "Year", "Daily_Precipitation": "Total Rainfall (mm)"},
                color="Daily_Precipitation",
                color_continuous_scale="Blues"
            )
            st.plotly_chart(fig_annual_rain, use_container_width=True)
            
            # Trend interpretation
            # Simple regression or just comparing first/last
            if len(annual_metrics) > 1:
                first_year = annual_metrics.iloc[0]["Daily_Precipitation"]
                last_complete_year = annual_metrics.iloc[-2]["Daily_Precipitation"] # Assuming current year is incomplete
                diff = last_complete_year - first_year
                if diff > 100:
                    st.write(f"ℹ️ **Trend:** Rainfall has increased by ~{diff:.0f}mm compared to the start of the period.")
                elif diff < -100:
                    st.write(f"ℹ️ **Trend:** Rainfall has decreased by ~{abs(diff):.0f}mm compared to the start of the period.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 2. Drought Frequency
            st.subheader("🌵 Drought Frequency")
            drought_counts = calculate_drought_frequency_yearly(df_history)
            
            if not drought_counts.empty:
                fig_drought = px.line(
                    drought_counts,
                    x=drought_counts.index,
                    y="Drought_Days",
                    title="Number of Drought Risk Days per Year",
                    labels={"index": "Year", "Drought_Days": "Days with Drought Risk"},
                    markers=True,
                    line_shape="spline"
                )
                fig_drought.update_traces(line_color="red")
                st.plotly_chart(fig_drought, use_container_width=True)
        
        with col2:
            # 3. Planting Season Onset
            st.subheader("🌱 Planting Season Onset")
            onsets = calculate_planting_onset(df_history)
            
            if not onsets.empty:
                fig_onset = px.scatter(
                    onsets,
                    x="Year",
                    y="Day_Of_Year",
                    title="Estimated Planting Start Date (Day of Year)",
                    labels={"Day_Of_Year": "Day of Year (1-365)"},
                    hover_data={"Onset_Date": "|%Y-%m-%d"}
                )
                # Add trendline
                fig_onset.add_trace(
                   go.Scatter(x=onsets["Year"], y=onsets["Day_Of_Year"], mode='lines', line=dict(dash='dot', color='green'), name='Trend')
                )
                
                st.plotly_chart(fig_onset, use_container_width=True)
                st.caption("*Onset defined as first date after Mar 1st with >20mm rain in 3 days.*")

        # 4. Crop GDD Comparison (Multi-year)
        st.subheader("☀️ Growing Degree Days (GDD) Accumulation by Year")
        crop_gdd_select = st.selectbox("Select Crop for GDD Trend:", list(CROP_PROFILES.keys()), key="gdd_trend_crop")
        t_base_trend = CROP_PROFILES[crop_gdd_select]["T_base"]
        
        # Calculate full GDD
        df_gdd_all = calculate_gdd(df_history, t_base_trend)
        
        if not df_gdd_all.empty:
            df_gdd_all["Year"] = df_gdd_all.index.year
            df_gdd_all["DayOfYear"] = df_gdd_all.index.dayofyear
            
            # Pivot for plotting
            # We want x=DayOfYear, y=Cumulative_GDD, color=Year
            # But Cumulative is continuous. We need cumulative RESET every year.
            
            # Recalculate cumulative GDD per year
            df_gdd_all["Annual_Cum_GDD"] = df_gdd_all.groupby("Year")["Daily_GDD"].cumsum()
            
            fig_gdd_trend = px.line(
                df_gdd_all,
                x="DayOfYear",
                y="Annual_Cum_GDD",
                color="Year",
                title=f"Cumulative GDD per Year for {crop_gdd_select} (T_base={t_base_trend}C)",
                labels={"Annual_Cum_GDD": "Cumulative GDD"},
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            st.plotly_chart(fig_gdd_trend, use_container_width=True)


# --- TAB 5: GDD Tracking ---
with tab5:
    st.header("🌱 Growing Degree Days (GDD) Tracking")

    crop_name = st.selectbox("Select Crop:", list(CROP_PROFILES.keys()))
    T_base = CROP_PROFILES[crop_name]["T_base"]

    st.info(
        f"Calculating GDD for **{crop_name}** using Base Temperature (T_base) = **{T_base}°C**"
    )

    df_gdd = calculate_gdd(df_zone, T_base)

    if df_gdd.empty:
        st.warning("Insufficient data for GDD calculation.")
    else:
        # Current GDD status
        current_gdd = df_gdd["Cumulative_GDD"].iloc[-1]
        target_gdd = CROP_PROFILES[crop_name].get("GDD_to_Maturity", 0)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("📊 Current Cumulative GDD", f"{current_gdd:.0f} °C-days")

        with col2:
            st.metric("🎯 GDD to Maturity", f"{target_gdd:.0f} °C-days")

        with col3:
            if target_gdd > 0:
                progress = (current_gdd / target_gdd) * 100
                st.metric("📈 Progress", f"{progress:.1f}%")

        # Visualization
        fig_gdd = px.line(
            df_gdd.tail(180).reset_index(),
            x="Timestamp",
            y="Cumulative_GDD",
            title=f"Cumulative GDD for {crop_name} (Last 6 Months)",
        )

        if target_gdd > 0:
            fig_gdd.add_hline(
                y=target_gdd,
                line_dash="dash",
                line_color="green",
                annotation_text="Maturity Target",
            )

        st.plotly_chart(fig_gdd, use_container_width=True)

        # Recent GDD data
        st.subheader("📅 Recent Daily GDD")
        st.dataframe(
            df_gdd[["Daily_GDD", "Cumulative_GDD"]]
            .tail(14)
            .style.format({"Daily_GDD": "{:.1f}", "Cumulative_GDD": "{:.1f}"}),
            use_container_width=True,
        )

# --- TAB 6: Crop Planning ---
with tab6:
    st.header("🗓️ Crop Planning & Suitability Analysis")
    
    # --- Comparative Analysis (Past vs Current vs Future) ---
    st.subheader("🔮 Integrated Season View (Past vs Current vs Future)")
    st.info("Compare this year's weather against the historical average and upcoming forecast.")
    
    # Prepare Data
    current_year = datetime.now().year
    
    # 1. Historical Baseline
    seasonality = calculate_historical_seasonality(df_raw[df_raw["Zone"] == selected_zone])
    
    # 2. Current Year Data
    df_current = df_zone[df_zone.index.year == current_year].copy()
    df_current_daily = calculate_daily_aggregates(df_current)
    if not df_current_daily.empty:
        df_current_daily["DayOfYear"] = df_current_daily.index.dayofyear
    
    # 3. Forecast Data
    # Reuse the forecast data fetched in Tab 2 if possible, or fetch new
    # For simplicity/robustness, we'll re-call the cached function
    df_forecast_daily = fetch_daily_forecast(selected_zone)
    if not df_forecast_daily.empty:
        df_forecast_daily["DayOfYear"] = df_forecast_daily["date"].apply(lambda x: x.timetuple().tm_yday)
    
    # --- Visualization: Temperature Trajectory ---
    fig_comp = go.Figure()
    
    # Historical Avg (Background)
    if not seasonality.empty:
        fig_comp.add_trace(go.Scatter(
            x=seasonality.index,
            y=seasonality["T_avg"],
            mode='lines',
            name='Historical Avg (Baseline)',
            line=dict(color='gray', width=2, dash='dash'),
            opacity=0.5
        ))
        
        # Add range (Min-Max) - Optional, adds complexity but good for context
        # fig_comp.add_trace(go.Scatter(
        #     x=seasonality.index, y=seasonality["T_max"], mode='lines', line=dict(width=0), showlegend=False
        # ))
        # fig_comp.add_trace(go.Scatter(
        #     x=seasonality.index, y=seasonality["T_min"], mode='lines', line=dict(width=0), 
        #     fill='tonexty', fillcolor='rgba(200, 200, 200, 0.2)', name='Historical Range'
        # ))

    # Current Year (Reference)
    if not df_current_daily.empty:
        fig_comp.add_trace(go.Scatter(
            x=df_current_daily["DayOfYear"],
            y=df_current_daily["T_avg"],
            mode='lines',
            name=f'{current_year} Actuals',
            line=dict(color='#2E7D32', width=3)
        ))
        
    # Forecast (Projection)
    if not df_forecast_daily.empty:
        # Connect forecast to last point of actuals if available to make it look continuous
        fig_comp.add_trace(go.Scatter(
            x=df_forecast_daily["DayOfYear"],
            y=df_forecast_daily["temp_max"], # Using Max temp for planning conservatism or Avg? Let's use avg if available. 
            # Note: fetch_daily_forecast returns temp_max/min. Let's approx avg.
            name='Forecast (Next 5 Days)',
            mode='lines+markers',
            line=dict(color='#FF6B6B', width=3, dash='dot')
        ))

    fig_comp.update_layout(
        title="Temperature Comparison: Past, Present, and Future",
        xaxis_title="Day of Year",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        xaxis=dict(range=[1, 366]) # Fixed range to show full year seasonality context? Or zoom to current?
        # Let's zoom to relevant window: current day +/- 60 days
    )
    
    # Dynamic Zoom
    today_doy = datetime.now().timetuple().tm_yday
    fig_comp.update_xaxes(range=[max(1, today_doy - 30), min(365, today_doy + 15)])
    
    st.plotly_chart(fig_comp, use_container_width=True)
    
    
    # --- Deviation Analysis (Metrics) ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Cumulative Rainfall Deviation")
        # Calc cumulative rain for current year vs baseline up to today
        if not seasonality.empty and not df_current_daily.empty:
            # Baseline cumsum (up to today)
            baseline_rain_ytd = seasonality[seasonality.index <= today_doy]["Daily_Precipitation"].sum()
            # Current cumsum
            current_rain_ytd = df_current_daily["Daily_Precipitation"].sum()
            
            diff = current_rain_ytd - baseline_rain_ytd
            pct_diff = (diff / baseline_rain_ytd * 100) if baseline_rain_ytd > 0 else 0
            
            st.metric(
                label=f"Rainfall YTD ({current_year}) vs Average",
                value=f"{current_rain_ytd:.1f} mm",
                delta=f"{diff:.1f} mm ({pct_diff:+.1f}%)"
            )
            
            if pct_diff < -20:
                st.warning("⚠️ **Drier than normal**. Consider water conservation or irrigation planning.")
            elif pct_diff > 20:
                st.info("💧 **Wetter than normal**. Monitor for waterlogging risks.")
            else:
                st.success("✅ Rainfall is tracking close to historical average.")
                
    with col2:
         st.subheader("🌡️ Heat Accumulation (GDD) Status")
         # Similar logic for GDD/Temp
         if not seasonality.empty and not df_current_daily.empty:
             baseline_temp_avg = seasonality[seasonality.index <= today_doy]["T_avg"].mean()
             current_temp_avg = df_current_daily["T_avg"].mean()
             
             temp_diff = current_temp_avg - baseline_temp_avg
             
             st.metric(
                 label="Avg Temp YTD vs Historical",
                 value=f"{current_temp_avg:.1f} °C",
                 delta=f"{temp_diff:+.1f} °C"
             )

    st.markdown("---")

    # Crop suitability (Existing Code)
    st.subheader("🌾 Crop Suitability Assessment")

    df_suggestions = suggest_crops(df_zone)

    if df_suggestions.empty:
        st.warning("Insufficient data for crop suitability analysis.")
    else:
        st.dataframe(df_suggestions, hide_index=True, use_container_width=True)

        st.info(
            "**Note:** Suitability is based on long-term temperature and rainfall "
            "matching to known crop requirements. 🟢 Highly Suitable meets all primary criteria."
        )

    st.markdown("---")

    # Planting window advisory
    st.subheader("📅 Planting Window Advisory")

    st.success(
        f"**ADVISORY for {selected_zone}:** Historical data suggests the most reliable "
        "primary planting window begins around **March 15** and closes by **April 30**."
    )

    st.info(
        "This window typically provides stable rainfall onset and sufficient soil "
        "temperature for germination. Always cross-reference with current year conditions."
    )

# --- TAB 7: Data Archive ---
with tab7:
    st.header("📁 Raw Data Archive")

    st.subheader(f"Recent Records for {selected_zone}")

    # Display options
    st.write(f"Displaying the latest {len(df_zone)} records from the archive.")
    
    st.dataframe(
        df_zone.tail(100)
        .reset_index()
        .style.format(
            {
                "Timestamp": lambda t: t.strftime("%Y-%m-%d %H:%M:%S"),
                "T_current": "{:.1f}°C",
                "Humidity": "{:.0f}%",
                "Precipitation_1h": "{:.1f} mm",
                "Wind_Speed": "{:.1f} m/s",
                # Add other columns as needed
            }
        ),
        use_container_width=True,
    )
    
    @st.cache_data
    def convert_df_to_csv(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv_data = convert_df_to_csv(df_zone)

    st.download_button(
        label="⬇️ Download Full Data (.csv)",
        data=csv_data,
        file_name=f"{selected_zone}_weather_data.csv",
        mime="text/csv",
    )
