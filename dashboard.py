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

# Import seasonal crop recommendation system
from seasonal_crops import SEASONAL_CROPS, get_current_season, get_crops_for_month, get_optimal_crops_for_month
from crop_recommender import get_crop_recommendations, get_planting_calendar, format_recommendation_display
from tts_utils import text_to_audio, autoplay_audio
from summary_generator import (
    generate_overview_summary,
    generate_temp_trend_summary,
    generate_wind_summary,
    generate_hourly_forecast_summary,
    generate_daily_forecast_summary,
    generate_drought_risk_summary,
    generate_crop_plan_summary
)
from auth import AuthManager
from sms_service import SMSService
from email_service import EmailService

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
    """Loads, cleans, and preprocesses weather data from both Supabase and local archive."""
    df_supabase = pd.DataFrame()
    df_local = pd.DataFrame()

    # 1. Try Loading from Supabase
    if SUPABASE_URL and SUPABASE_KEY and create_client:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table("weather_data").select("*").execute()
            
            if response.data:
                df_supabase = pd.DataFrame(response.data)
                
                # Column mapping
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
                df_supabase.rename(columns=column_map, inplace=True)
                
                # Check for critical column "Timestamp"
                if "Timestamp" in df_supabase.columns:
                     df_supabase["Timestamp"] = pd.to_datetime(df_supabase["Timestamp"])
                     # Ensure timezone-naive for compatibility
                     if pd.api.types.is_datetime64_any_dtype(df_supabase["Timestamp"]):
                        # Handle potential mixed bag or just convert
                        # If it's already naive, this might error if we use tz_convert, so use tz_localize(None)
                        # But first ensure it is dt accessible
                        if df_supabase["Timestamp"].dt.tz is not None:
                             df_supabase["Timestamp"] = df_supabase["Timestamp"].dt.tz_localize(None)
                     
                     df_supabase.set_index("Timestamp", inplace=True)
                else:
                    st.warning("⚠️ Supabase data missing 'Timestamp' column.")
                    df_supabase = pd.DataFrame() # Invalidate if structure is wrong

        except Exception as e:
            st.warning(f"⚠️ Could not load from Supabase: {e}")

    # 2. Try Loading from Local CSV
    if os.path.exists(DATA_ARCHIVE_FILE):
        try:
            df_local = pd.read_csv(DATA_ARCHIVE_FILE)
            if "Timestamp" in df_local.columns:
                df_local["Timestamp"] = pd.to_datetime(df_local["Timestamp"])
                # Ensure timezone-naive for compatibility
                if df_local["Timestamp"].dt.tz is not None:
                     df_local["Timestamp"] = df_local["Timestamp"].dt.tz_localize(None)
                
                df_local.set_index("Timestamp", inplace=True)
        except Exception as e:
            st.error(f"❌ Error loading local data: {e}")

    # 3. Combine Data sources
    if df_supabase.empty and df_local.empty:
        # Fallback: Generate Sample Data for Demo purposes if no source available
        if not os.path.exists(DATA_ARCHIVE_FILE):
             st.warning(
                "⚠️ No live or archived data found (Supabase/Local). Generating SAMPLE data for demonstration."
            )
             # Generate 90 days of sample data
             dates = pd.date_range(end=datetime.now(), periods=24*90, freq="h")
             
             sample_data = []
             for zone in AGRICULTURAL_ZONES.keys():
                 for date in dates:
                     # Simple synthetic weather
                     hour = date.hour
                     base_temp = 25 + (5 * np.sin((hour - 6) * np.pi / 12))  # Daily cycle
                     noise = np.random.normal(0, 2)
                     
                     sample_data.append({
                         "Timestamp": date,
                         "Zone": zone,
                         "T_current": base_temp + noise,
                         "T_min": base_temp - 2,
                         "T_max": base_temp + 2,
                         "Humidity": 60 + (20 * np.cos((hour - 6) * np.pi / 12)) + noise,
                         "Precipitation_1h": max(0, np.random.normal(0, 1) if np.random.random() > 0.8 else 0),
                         "Wind_Speed": max(0, 5 + np.random.normal(0, 2)),
                         "Weather_Condition": "Clouds" if np.random.random() > 0.5 else "Clear"
                     })
                     
             df_sample = pd.DataFrame(sample_data)
             df_sample.set_index("Timestamp", inplace=True)
             return df_sample

        return pd.DataFrame()

    df_combined = pd.concat([df_supabase, df_local])

    # 4. Clean and Deduplicate
    try:
        # Ensure consistent schema before processing
        numeric_cols = [
            "T_current", "T_min", "T_max", "Humidity", 
            "Precipitation_1h", "Precipitation_3h"
        ]
        
        for col in numeric_cols:
            if col in df_combined.columns:
                df_combined[col] = pd.to_numeric(df_combined[col], errors="coerce")
        
        # Drop rows with missing critical data
        df_combined.dropna(subset=["T_min", "T_max"], inplace=True)
        
        # Remove duplicates (preferring local or simply latest)
        # Reset index to deduplicate by Timestamp + Zone
        df_combined.reset_index(inplace=True)
        df_combined.drop_duplicates(subset=["Timestamp", "Zone"], keep="last", inplace=True)
        df_combined.set_index("Timestamp", inplace=True)
        
        df_combined.sort_index(inplace=True)
        
        return df_combined

    except Exception as e:
        st.error(f"❌ Error processing combined data: {e}")
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
    
    # Filter out years with insufficient data (less than 6 months = 180 days)
    # Count number of days per year in the original data
    days_per_year = daily.groupby(daily.index.year).size()
    
    # Only keep years with at least 180 days of data
    valid_years = days_per_year[days_per_year >= 180].index
    annual = annual[annual.index.isin(valid_years)]
    
    return annual


def calculate_planting_onset(df_zone):
    """
    Identify potential planting onset date for each year.
    Heuristic: First day after March 1st with > 20mm rain in 3 days.
    """
    daily = calculate_daily_aggregates(df_zone)
    if daily.empty:
        return pd.DataFrame()
    
    # Filter out years with insufficient data (less than 6 months = 180 days)
    days_per_year = daily.groupby(daily.index.year).size()
    valid_years = days_per_year[days_per_year >= 180].index
        
    onsets = []
    years = daily.index.year.unique()
    
    for year in years:
        # Skip years with insufficient data
        if year not in valid_years:
            continue
            
        # Filter for planting window (March - June)
        start_date = pd.Timestamp(f"{year}-03-01")
        if daily.index.tz is not None:
            start_date = start_date.tz_localize(daily.index.tz)
            
        mask = (daily.index >= start_date) & (daily.index.year == year)
        season_data = daily[mask].copy()
        
        # Rolling 3-day rainfall
        season_data["Rain_3D"] = season_data["Daily_Precipitation"].rolling(3).sum()
        
        # Find first occurrence >= 20mm
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
    
    # Filter out years with insufficient data (less than 6 months = 180 days)
    # Count total days per year in original data
    daily = calculate_daily_aggregates(df_zone)
    if not daily.empty:
        days_per_year = daily.groupby(daily.index.year).size()
        valid_years = days_per_year[days_per_year >= 180].index
        yearly_droughts = yearly_droughts[yearly_droughts.index.isin(valid_years)]
    
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

# Initialize Auth
auth = AuthManager()

# Session State for User
if "user" not in st.session_state:
    st.session_state["user"] = None

# --- Authentication Flow ---
if not st.session_state["user"]:
    col1, col2 = st.columns([1, 2]) # Adjust layout as needed, maybe centered

    with col2:
        st.title("🌾 Abia State ADSS")
        st.subheader("Login or Sign Up to access the dashboard.")
        
        auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
        
        with auth_tab1:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    result = auth.sign_in(email, password)
                    if result.get("success"):
                        st.session_state["user"] = result["user"]
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(result.get("error"))
        
        with auth_tab2:
            with st.form("signup_form"):
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                # confirm_password = st.text_input("Confirm Password", type="password") # Optional
                submit_signup = st.form_submit_button("Sign Up")
                
                if submit_signup:
                    result = auth.sign_up(new_email, new_password)
                    if result.get("success"):
                         st.success(result["message"])
                    else:
                        st.error(result.get("error"))

    st.stop() # Stop execution if not logged in

# --- LOGOUT BUTTON (Sidebar) ---
with st.sidebar:
    # st.sidebar is accessible anywhere
    st.markdown(f"**User:** {st.session_state['user'].email if hasattr(st.session_state['user'], 'email') else 'Logged In'}")
    
    with st.expander("📱 SMS & 📧 Email Alerts"):
        # SMS
        st.caption("SMS Setup")
        sms_service = SMSService()
        phone_number = st.text_input("Phone Number", key="user_phone", placeholder="234...")
        
        # Email
        st.caption("Email Setup")
        email_service = EmailService()
        email_address = st.text_input("Email Address", key="user_email_alert", placeholder="you@example.com")

        if st.button("Send Test Alerts"):
            # Test SMS
            if phone_number:
                with st.spinner("Sending Test SMS..."):
                    res = sms_service.send_alert(phone_number, "Test SMS from Abia ADSS.")
                    if res.get("success"):
                        st.success("✅ SMS Sent!")
                    else:
                        st.error(f"❌ SMS Failed: {res.get('error')}")
            
            # Test Email
            if email_address:
                with st.spinner("Sending Test Email..."):
                    res = email_service.send_alert(email_address, "Test Email from Abia ADSS", "This is a test email alert.")
                    if res.get("success"):
                         st.success("✅ Email Sent!")
                    else:
                        st.error(f"❌ Email Failed: {res.get('error')}")

    if st.button("Logout", key="logout_btn"):
        auth.sign_out()
        st.session_state["user"] = None
        st.rerun()
    st.markdown("---")


# Load data
df_raw = load_data()

if df_raw.empty:
    st.stop()

# --- HEADER ---
st.markdown("""
    <style>
    .main-title {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .subtitle {
        font-size: 1.3rem;
        text-align: center;
        color: #A0A0A0;
        margin-bottom: 2rem;
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    </style>
    <h1 class="main-title">🌾 Abia State Agricultural Decision Support System</h1>
    <p class="subtitle">Real-time weather analytics and crop management advisory for agricultural zones</p>
""", unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/tractor.png", width=50)
    st.title("Agro-Manager")
    
    st.markdown("---")

# Audio Welcome
welcome_text = "Welcome to the Abia State Agricultural System. I can help you plan your farm activities."
if st.button("🔊 Read Welcome Message"):
    audio = text_to_audio(welcome_text)
    autoplay_audio(audio)

st.markdown("---")

# --- Navigation & Controls (Main Top Bar) ---
# Create a container for controls to make them prominent
st.markdown("""<div style="background-color: #161b22; padding: 1rem; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 2rem;">""", unsafe_allow_html=True)

col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 1])

with col_nav1:
    st.markdown("### 📍 Weather Station")
    st.caption("Select your zone below") 
    # Language selector removed from here (moved to sidebar)

with col_nav2:
    unique_zones = sorted(df_raw["Zone"].unique())
    # Use session state key to preserve selection
    selected_zone = st.selectbox(
        "Select Agricultural Zone:", 
        unique_zones,
        key="selected_zone"
    )

with col_nav3:
    date_range = st.selectbox(
        "Select Timeframe:",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Data"],
        index=2,
        key="date_range"
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
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📊 Overview & Trends",
        "🔮 Weather Forecast",
        "📜 Historical Trends",
        "💧 Risk Analysis",
        "🗓️ Crop Planning",
        "📁 Data Archive",
    ]
)

# --- TAB 1: Overview & Trends (Logic is complete) ---
with tab1:
    st.header(f"📊 Weather Overview for {selected_zone}")
    
    # Farmer-friendly introduction
    st.info("👨‍🌾 **What This Shows:** Current weather conditions and recent trends in your area. Use this to plan daily farm activities like irrigation, spraying, or harvesting.")

    if not df_zone.empty:
        latest = df_zone.iloc[-1]
        
        # Construct summary text
        temp_status = "hot" if latest['T_current'] > 30 else "mild"
        rain_status = "raining" if latest.get("Precipitation_1h", 0) > 0 else "dry"
        
        # Helper to get full summary
        def get_summary():
            return generate_overview_summary(selected_zone, latest, calculate_statistics(df_zone))

        col_audio, col_sms, col_email = st.columns([1, 1, 1])
        with col_audio:
            if st.button("🔊 Listen"):
                summary_text = get_summary()
                audio = text_to_audio(summary_text)
                autoplay_audio(audio)
        
        with col_sms:
            if st.button("📱 SMS Summary"):
                phone = st.session_state.get("user_phone")
                if not phone:
                     st.error("Set phone in Sidebar.")
                else:
                    with st.spinner("Sending SMS..."):
                        sms_msg = get_summary()
                        sms_svc = SMSService()
                        res = sms_svc.send_alert(phone, sms_msg)
                        if res.get("success"):
                            st.success("✅ SMS Sent!")
                        else:
                            st.error(f"❌ SMS Failed: {res.get('error')}")

        with col_email:
             if st.button("📧 Email Summary"):
                email_addr = st.session_state.get("user_email_alert")
                if not email_addr:
                     st.error("Set email in Sidebar.")
                else:
                    with st.spinner("Sending Email..."):
                        email_msg = get_summary()
                        email_svc = EmailService()
                        res = email_svc.send_alert(
                            email_addr, 
                            f"Abia ADSS Weather Update: {selected_zone}", 
                            email_msg
                        )
                        if res.get("success"):
                            st.success("✅ Email Sent!")
                        else:
                            st.error(f"❌ Email Failed: {res.get('error')}")

    if df_zone.empty:
        st.warning("No data available for the selected zone and timeframe.")
    else:
        # Latest conditions
        latest = df_zone.iloc[-1]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            temp_current = latest['T_current']
            st.metric(
                "🌡️ Current Temperature",
                f"{temp_current:.1f} °C",
                delta=f"{temp_current - df_zone['T_current'].mean():.1f}°C vs avg",
            )
            # Dynamic explanation based on temperature value
            if temp_current > 35:
                st.warning("⚠️ **Very hot!** Heat stress risk for crops. Increase watering and provide shade if possible.")
            elif temp_current > 30:
                st.info("☀️ **Hot weather.** Good for heat-loving crops. Ensure adequate irrigation.")
            elif temp_current >= 20:
                st.success("✅ **Ideal temperature** for most crops. Good growing conditions.")
            elif temp_current >= 15:
                st.info("🌤️ **Mild weather.** Suitable for cool-season crops.")
            else:
                st.warning("❄️ **Cold weather.** Risk of frost damage. Protect sensitive crops.")

        with col2:
            humidity = latest['Humidity']
            st.metric("💧 Humidity", f"{humidity:.0f}%")
            # Dynamic explanation based on humidity value
            if humidity > 80:
                st.warning("⚠️ **High humidity.** Increased risk of fungal diseases. Improve air circulation.")
            elif humidity >= 60:
                st.success("✅ **Good humidity** for most crops. Comfortable growing conditions.")
            elif humidity >= 40:
                st.info("🌤️ **Moderate humidity.** Monitor soil moisture regularly.")
            else:
                st.warning("🏜️ **Low humidity.** Plants may need more frequent watering.")

        with col3:
            rain_value = latest.get("Precipitation_1h", 0.0)
            st.metric("🌧️ Last Hour Rain", f"{rain_value:.1f} mm")
            # Dynamic explanation based on rainfall
            if rain_value > 10:
                st.warning("🌧️ **Heavy rain!** Delay field work. Check for waterlogging.")
            elif rain_value > 2:
                st.info("🌦️ **Moderate rain.** Good for crops. Avoid spraying pesticides.")
            elif rain_value > 0:
                st.success("💧 **Light rain.** Beneficial for crops. Reduces irrigation needs.")
            else:
                # Check recent rainfall pattern
                recent_rain = df_zone.tail(24)["Precipitation_1h"].sum()
                if recent_rain < 1:
                    st.info("☀️ **No recent rain.** Monitor soil moisture and irrigate if needed.")
                else:
                    st.success("✅ **Dry now** but recent rain was good. Soil should have moisture.")

        with col4:
            if "Wind_Speed" in latest:
                wind_speed = latest['Wind_Speed']
                st.metric("💨 Wind Speed", f"{wind_speed:.1f} m/s")
                # Dynamic explanation based on wind speed
                if wind_speed > 10:
                    st.error("🌪️ **Very windy!** Risk of crop damage. Avoid spraying. Secure structures.")
                elif wind_speed > 5:
                    st.warning("💨 **Windy conditions.** Not ideal for spraying pesticides.")
                elif wind_speed > 2:
                    st.success("🍃 **Gentle breeze.** Good air circulation for crops.")
                else:
                    st.info("😌 **Calm conditions.** Good for spraying and field work.")

        st.markdown("---")

        # Statistics
        stats = calculate_statistics(df_zone)

        if stats:
            st.subheader("📈 Statistical Summary")
            if st.button("🔊 Listen to Stats"):
                 stats_text = f"Statistical Summary. Average temperature is {stats['avg_temp']:.1f} degrees. Maximum reached {stats['max_temp']:.1f} degrees. Total rain in last 30 days is {stats['total_rain_30d']:.1f} millimeters."
                 autoplay_audio(text_to_audio(stats_text))

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Temperature Statistics**")
                st.write(f"Average: {stats['avg_temp']:.1f}°C")
                st.write(f"Maximum: {stats['max_temp']:.1f}°C")
                st.write(f"Minimum: {stats['min_temp']:.1f}°C")

            with col2:
                st.markdown("**Rainfall Summary**")
                rain_30d = stats['total_rain_30d']
                st.write(f"Last 30 days: {rain_30d:.1f} mm")
                st.write(f"Last 90 days: {stats['total_rain_90d']:.1f} mm")
                st.write(f"Daily average: {stats['avg_daily_rain']:.1f} mm")
                
                # Dynamic explanation based on 30-day rainfall
                if rain_30d < 50:
                    st.warning("⚠️ **Low rainfall** in past month. Increase irrigation frequency.")
                elif rain_30d < 100:
                    st.info("💧 **Below average rain.** Monitor soil moisture and irrigate as needed.")
                elif rain_30d <= 200:
                    st.success("✅ **Good rainfall** for most crops. Soil moisture should be adequate.")
                else:
                    st.warning("🌧️ **Heavy rainfall.** Watch for waterlogging and drainage issues.")

            with col3:
                st.markdown("**Other Metrics**")
                st.write(f"Avg Humidity: {stats['avg_humidity']:.1f}%")

        # Temperature trend
        st.subheader("🌡️ Temperature Trends")
        if st.button("🔊 Listen to Trends"):
             trend_text = generate_temp_trend_summary(df_zone)
             autoplay_audio(text_to_audio(trend_text))
        
        with st.expander("ℹ️ How to Read This Chart"):
            st.write("""
            **What it shows:** Daily high (red), current (orange), and low (blue) temperatures over time.
            
            **How to use it:**
            - **Red line (Max):** Highest temperature each day - important for heat stress on crops
            - **Blue line (Min):** Lowest temperature each day - watch for cold that might damage crops
            - **Orange line (Current):** Average temperature - shows overall temperature patterns
            
            **For farming:** Use this to spot temperature patterns and plan activities like planting or protecting crops from extreme heat or cold.
            """)

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
        if st.button("🔊 Listen to Wind Analysis"):
             wind_text = generate_wind_summary(df_zone)
             autoplay_audio(text_to_audio(wind_text))
        st.caption("💡 Wind direction and pressure help predict upcoming weather changes. Falling pressure often means rain is coming.")
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
        
        # Add detailed analysis below the charts
        st.markdown("---")
        st.markdown("### 📊 Detailed Analysis & Insights")
        
        col_analysis1, col_analysis2 = st.columns(2)
        
        with col_analysis1:
            st.markdown("**🌬️ Wind Pattern Analysis**")
            
            # Calculate wind statistics
            df_wind = df_zone.tail(24)
            avg_speed = df_wind["Wind_Speed"].mean()
            max_speed = df_wind["Wind_Speed"].max()
            min_speed = df_wind["Wind_Speed"].min()
            
            # Determine predominant direction
            def get_cardinal_direction(degrees):
                directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
                idx = int((degrees + 22.5) / 45) % 8
                return directions[idx]
            
            cardinal_dirs = [get_cardinal_direction(d) for d in df_wind["Wind_Direction"].values]
            from collections import Counter
            most_common = Counter(cardinal_dirs).most_common(2)
            predominant_dir = most_common[0][0] if most_common else "Variable"
            predominant_pct = (most_common[0][1] / len(cardinal_dirs) * 100) if most_common else 0
            
            st.write(f"**Wind Statistics (Last 24h):**")
            st.write(f"- Predominant Direction: **{predominant_dir}** ({predominant_pct:.0f}% of time)")
            st.write(f"- Average Speed: **{avg_speed:.1f} m/s**")
            st.write(f"- Speed Range: {min_speed:.1f} - {max_speed:.1f} m/s")
            
            # Wind consistency
            speed_std = df_wind["Wind_Speed"].std()
            if speed_std < 1:
                consistency = "Very Consistent"
                consistency_icon = "✅"
            elif speed_std < 2:
                consistency = "Moderately Consistent"
                consistency_icon = "🔄"
            else:
                consistency = "Variable"
                consistency_icon = "⚠️"
            
            st.write(f"- Wind Consistency: {consistency_icon} **{consistency}**")
            
            # Farming implications
            st.markdown("**🌾 Farming Implications:**")
            
            if avg_speed > 7:
                st.error("🌪️ **Very High Winds** - Avoid all field work. Risk of crop damage and soil erosion.")
            elif avg_speed > 5:
                st.warning("💨 **High Winds** - Not suitable for spraying. Delay pesticide/herbicide application.")
            elif avg_speed >= 2 and avg_speed <= 5:
                st.success("✅ **Ideal Winds** - Good air circulation reduces disease risk. Suitable for most farm activities.")
            else:
                st.info("🍃 **Light Winds** - Excellent for spraying. Minimal drift risk.")
            
            # Direction-based weather prediction
            if predominant_dir in ['E', 'SE', 'S', 'SW']:
                st.info(f"💧 **{predominant_dir} winds** typically bring moisture from the ocean. Monitor for potential rainfall.")
            elif predominant_dir in ['N', 'NE', 'NW']:
                st.info(f"🌤️ **{predominant_dir} winds** usually bring drier, cooler air. Expect clearer conditions.")
            elif predominant_dir == 'W':
                st.info(f"⛅ **{predominant_dir} winds** can bring variable weather. Stay alert to changes.")
        
        with col_analysis2:
            st.markdown("**🌡️ Atmospheric Pressure Analysis**")
            
            # Pressure statistics
            current_pressure = df_zone["Pressure"].iloc[-1]
            pressure_24h_ago = df_zone["Pressure"].iloc[-24] if len(df_zone) >= 24 else df_zone["Pressure"].iloc[0]
            pressure_change_24h = current_pressure - pressure_24h_ago
            
            # Calculate 6-hour trend
            if len(df_zone) >= 6:
                pressure_6h_ago = df_zone["Pressure"].iloc[-6]
                pressure_change_6h = current_pressure - pressure_6h_ago
                trend_6h = "Rising" if pressure_change_6h > 0.5 else "Falling" if pressure_change_6h < -0.5 else "Stable"
            else:
                pressure_change_6h = 0
                trend_6h = "Insufficient data"
            
            st.write(f"**Pressure Metrics:**")
            st.write(f"- Current: **{current_pressure:.1f} hPa**")
            st.write(f"- 24h Change: **{pressure_change_24h:+.1f} hPa**")
            st.write(f"- 6h Trend: **{trend_6h}** ({pressure_change_6h:+.1f} hPa)")
            
            # Pressure classification
            if current_pressure < 1000:
                pressure_class = "Low Pressure System"
                pressure_icon = "🌧️"
            elif current_pressure > 1020:
                pressure_class = "High Pressure System"
                pressure_icon = "☀️"
            else:
                pressure_class = "Normal Pressure"
                pressure_icon = "⛅"
            
            st.write(f"- System Type: {pressure_icon} **{pressure_class}**")
            
            # Weather prediction
            st.markdown("**🔮 Weather Forecast:**")
            
            if pressure_change_24h < -5:
                st.error("⛈️ **Rapidly Falling** - Severe weather likely! Expect heavy rain or storms within 12-24 hours.")
                st.write("**Actions:** Secure equipment, check drainage, postpone all field work.")
            elif pressure_change_24h < -2:
                st.warning("🌧️ **Falling Pressure** - Weather deteriorating. Rain expected within 24-48 hours.")
                st.write("**Actions:** Complete urgent outdoor tasks, prepare for wet conditions.")
            elif pressure_change_24h > 5:
                st.success("🌤️ **Rapidly Rising** - Weather clearing quickly! Expect sunny, dry conditions.")
                st.write("**Actions:** Excellent time for harvesting, spraying, and field work.")
            elif pressure_change_24h > 2:
                st.success("☀️ **Rising Pressure** - Weather improving. Conditions becoming more stable.")
                st.write("**Actions:** Good time to plan outdoor activities.")
            else:
                st.info("➡️ **Stable Pressure** - Weather conditions steady. No major changes expected.")
                st.write("**Actions:** Continue normal farm operations.")
            
            # Additional context
            if current_pressure < 995:
                st.caption("⚠️ Very low pressure - associated with storms and heavy rainfall.")
            elif current_pressure > 1025:
                st.caption("ℹ️ Very high pressure - associated with clear skies and dry weather.")

# --- TAB 2: Weather Forecast (Enhanced to match screenshot) ---
with tab2:
    st.header(f"🔮 Weather Forecast for {selected_zone}")
    
    st.info("👨‍🌾 **What This Shows:** Weather predictions for the next 2 days (hourly) and 5 days (daily). Use this to plan farm work like planting, spraying pesticides, or harvesting. Avoid spraying before rain!")
    
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
            if st.button("🔊 Listen to Hourly Forecast"):
                 forecast_text = generate_hourly_forecast_summary(df_hourly)
                 autoplay_audio(text_to_audio(forecast_text))
            st.caption("💡 **For farmers:** Check hourly forecasts before spraying crops or doing outdoor work. High rain probability (>60%) means postpone spraying.")
            
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
            if st.button("🔊 Listen to Daily Forecast"):
                 daily_text = generate_daily_forecast_summary(df_daily)
                 autoplay_audio(text_to_audio(daily_text))
            st.caption("💡 **For farmers:** Use this to plan your week. Look for dry days for harvesting and rainy days to avoid field work.")
            
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
    
    st.info("👨‍🌾 **What This Shows:** Drought and waterlogging risks based on recent rainfall. This helps you protect your crops by taking action early (irrigation for drought, drainage for waterlogging).")

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
            st.warning("👨‍🌾 **What to do:** Your crops may not have enough water. Start irrigation immediately, especially for young plants. Check soil moisture daily.")
        elif latest_risk["Risk_Flag"] == "Waterlogging Risk":
            st.error(
                f"⚠️ **WATERLOGGING ALERT**: 7-day rainfall is {latest_risk['Rain_7D_Sum']:.1f} mm "
                f"(threshold: ≥ {WET_THRESHOLD} mm). Monitor for crop disease."
            )
            st.warning("👨‍🌾 **What to do:** Too much water can damage crop roots and cause diseases. Improve drainage, avoid adding more water, and watch for fungal diseases on leaves.")
        else:
            st.success(
                f"✅ **NORMAL CONDITIONS**: 7-day rainfall is {latest_risk['Rain_7D_Sum']:.1f} mm. "
                "No immediate risk detected."
            )
            st.info("👨‍🌾 **What to do:** Conditions are good for farming. Continue normal watering and farming activities.")

        # Visualization
        st.subheader("📊 Rainfall and Risk Trends")
        if st.button("🔊 Listen to Risk Analysis"):
             risk_text = generate_drought_risk_summary(latest_risk)
             autoplay_audio(text_to_audio(risk_text))

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
        st.caption("💡 **For farmers:** The gauge shows total rain in the last 7 days. Green zone = good. Red zone (left) = too dry, need irrigation. Blue zone (right) = too wet, improve drainage.")
        
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
    st.info("👨‍🌾 **What This Shows:** Long-term weather patterns from past years. Use this to understand how weather is changing and plan for future seasons based on historical patterns.")
    
    # Use full dataset for historical trends, ignoring the sidebar date filter
    df_history = df_raw[df_raw["Zone"] == selected_zone].copy()
    
    if df_history.empty:
        st.warning("Insufficient data for trend analysis.")
    else:
        # 1. Monthly Rainfall Accumulation
        st.subheader("🌧️ Rainfall Accumulation Over Time")
        if st.button("🔊 Listen to Historical Rain"):
             from summary_generator import generate_historical_rain_summary 
             # Local import or use global if already imported. I globally imported it earlier but let's be safe.
             hist_text = generate_historical_rain_summary(rain_df if 'rain_df' in locals() else None)
             autoplay_audio(text_to_audio(hist_text))
        
        with st.expander("ℹ️ How to Read This Chart"):
            st.write("""
            **What it shows:** Total rainfall accumulated each month over time.
            
            **How to use it:**
            - **Higher bars** = More rain that month (good for water-loving crops)
            - **Lower bars** = Less rain that month (may need more irrigation)
            - **Continuous timeline** = Shows rainfall patterns month by month
            
            **For farming:** Compare rainfall across months to identify wet and dry periods. Plan irrigation and crop selection based on these patterns.
            """)
        
        # Calculate monthly rainfall
        daily = calculate_daily_aggregates(df_history)
        if not daily.empty:
            # Filter out incomplete years
            days_per_year = daily.groupby(daily.index.year).size()
            valid_years = days_per_year[days_per_year >= 180].index
            daily_filtered = daily[daily.index.year.isin(valid_years)]
            
            # Group by month
            monthly_rain = daily_filtered.resample("M").agg({
                "Daily_Precipitation": "sum"
            })
            
            if not monthly_rain.empty:
                # Create DataFrame for plotting
                rain_df = pd.DataFrame({
                    "Date": monthly_rain.index,
                    "Rainfall": monthly_rain["Daily_Precipitation"].values
                })
                
                fig_monthly_rain = px.bar(
                    rain_df,
                    x="Date",
                    y="Rainfall",
                    title="Monthly Rainfall (mm)",
                    labels={"Date": "Month", "Rainfall": "Total Rainfall (mm)"},
                    color="Rainfall",
                    color_continuous_scale="Blues"
                )
                # Format x-axis to show month-year labels
                fig_monthly_rain.update_xaxes(
                    tickformat="%b %Y",  # Display as "Jan 2024", "Feb 2024", etc.
                    dtick="M1"  # One tick per month
                )
                st.plotly_chart(fig_monthly_rain, use_container_width=True)
                
                # Trend interpretation
                if len(rain_df) > 3:
                    recent_avg = rain_df.tail(3)["Rainfall"].mean()
                    earlier_avg = rain_df.head(3)["Rainfall"].mean()
                    diff = recent_avg - earlier_avg
                    if diff > 20:
                        st.write(f"ℹ️ **Trend:** Recent months show ~{diff:.0f}mm more rainfall on average compared to earlier months.")
                    elif diff < -20:
                        st.write(f"ℹ️ **Trend:** Recent months show ~{abs(diff):.0f}mm less rainfall on average compared to earlier months.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 2. Drought Frequency
            st.subheader("🌵 Drought Frequency")
            if st.button("🔊 Listen to Drought Stats"):
                 drought_text = "Drought Frequency Analysis. This chart shows the number of dry days per month. High bars indicate periods of water stress."
                 autoplay_audio(text_to_audio(drought_text))
            st.caption("💡 **For farmers:** Shows how many dry days occurred each month. More drought days = higher risk of crop water stress. Plan irrigation accordingly.")
            
            # Get drought risk data
            df_risk = identify_wet_dry_periods(df_history)
            
            if not df_risk.empty:
                # Filter for drought days
                drought_days = df_risk[df_risk["Risk_Flag"] == "Drought Risk"]
                
                # Group by month instead of year for continuous timeline
                monthly_droughts = drought_days.resample("M").size()
                
                # Filter out months with no data or from incomplete years
                daily = calculate_daily_aggregates(df_history)
                if not daily.empty:
                    days_per_year = daily.groupby(daily.index.year).size()
                    valid_years = days_per_year[days_per_year >= 180].index
                    monthly_droughts = monthly_droughts[monthly_droughts.index.year.isin(valid_years)]
                
                if not monthly_droughts.empty:
                    # Create DataFrame for plotting
                    drought_df = pd.DataFrame({
                        "Date": monthly_droughts.index,
                        "Drought_Days": monthly_droughts.values
                    })
                    
                    fig_drought = px.line(
                        drought_df,
                        x="Date",
                        y="Drought_Days",
                        title="Number of Drought Risk Days per Month",
                        labels={"Date": "Month", "Drought_Days": "Days with Drought Risk"},
                        markers=True
                    )
                    fig_drought.update_traces(line_color="red")
                    # Format x-axis to show month-year labels
                    fig_drought.update_xaxes(
                        tickformat="%b %Y",  # Display as "Jan 2024", "Feb 2024", etc.
                        dtick="M1"  # One tick per month
                    )
                    st.plotly_chart(fig_drought, use_container_width=True)
        
        with col2:
            # 3. Planting Season Onset
            st.subheader("🌱 Planting Season Onset")
            if st.button("🔊 Listen to Onset Advice"):
                 onset_text = "Planting Season Onset. This shows when the rains typically start. Use this to determine the best week to plant your crops."
                 autoplay_audio(text_to_audio(onset_text))
            st.caption("💡 **For farmers:** Shows when the rainy season typically starts each year (after March 1st). Use this to plan your planting dates. Earlier onset = plant earlier.")
            onsets = calculate_planting_onset(df_history)
            
            if not onsets.empty:
                fig_onset = px.scatter(
                    onsets,
                    x="Year",
                    y="Day_Of_Year",
                    title="Estimated Planting Start Date (Day of Year)",
                    labels={"Day_Of_Year": "Day of Year (1-365)", "Year": "Year"},
                    hover_data={"Onset_Date": "|%Y-%m-%d"}
                )
                # Add trendline
                fig_onset.add_trace(
                   go.Scatter(x=onsets["Year"], y=onsets["Day_Of_Year"], mode='lines', line=dict(dash='dot', color='green'), name='Trend')
                )
                
                # Format x-axis to show clean year labels (2024, 2025) instead of decimals
                fig_onset.update_xaxes(
                    tickmode='linear',
                    dtick=1,
                    tickformat='d'  # Display as integers
                )
                
                st.plotly_chart(fig_onset, use_container_width=True)
                st.caption("*Onset defined as first date after Mar 1st with >20mm rain in 3 days.*")

        # 4. Crop GDD Comparison (Multi-year)
        st.subheader("☀️ Growing Degree Days (GDD) Accumulation by Year")
        st.caption("💡 **For farmers:** GDD measures heat available for crop growth. Compare different years to see which had better growing conditions.")
        crop_gdd_select = st.selectbox("Select Crop for GDD Trend:", list(SEASONAL_CROPS.keys()), key="gdd_trend_crop")
        t_base_trend = SEASONAL_CROPS[crop_gdd_select]["T_base"]
        
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

        

                


                

# --- TAB 5: Crop Planning ---
with tab5:
    st.header("🗓️ Crop Planning & Suitability Analysis")
    
    st.info("👨‍🌾 **What This Shows:** Recommendations on which crops to plant based on your area's weather conditions. Also compares current weather to historical patterns to help you plan better.")
    
    # --- Comparative Analysis (Past vs Current vs Future) ---
    st.subheader("🔮 Integrated Season View (Past vs Current vs Future)")
    st.caption("💡 **For farmers:** Compare this year's weather (green) to past years' average (gray) and upcoming forecast (blue). This helps you know if this year is warmer, cooler, wetter, or drier than normal.")
    
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
        xaxis_title="Time of Year",
        yaxis_title="Temperature (°C)",
        hovermode="x unified",
        xaxis=dict(range=[1, 366]) # Fixed range to show full year seasonality context? Or zoom to current?
        # Let's zoom to relevant window: current day +/- 60 days
    )
    
    # Dynamic Zoom
    today_doy = datetime.now().timetuple().tm_yday
    fig_comp.update_xaxes(range=[max(1, today_doy - 30), min(365, today_doy + 15)])
    
    # Convert day-of-year to actual date ranges for better readability
    # Get current year for date conversion
    current_year = datetime.now().year
    
    # Create function to convert day-of-year to date
    def doy_to_date(day_of_year, year=current_year):
        """Convert day of year to actual date"""
        date = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
        return date.strftime("%b %d")  # e.g., "Nov 16"
    
    # Generate tick values every 10 days within the visible range
    visible_start = max(1, today_doy - 30)
    visible_end = min(365, today_doy + 15)
    tick_vals = list(range(visible_start, visible_end + 1, 10))
    
    # Convert to date ranges (e.g., "Nov 09 - Nov 19")
    tick_text = []
    for day in tick_vals:
        start_date = doy_to_date(day)
        end_date = doy_to_date(min(day + 9, 365))  # 10-day range
        tick_text.append(f"{start_date} - {end_date}")
    
    # Update x-axis to show date ranges
    fig_comp.update_xaxes(
        tickmode='array',
        tickvals=tick_vals,
        ticktext=tick_text,
        title="Date Range (10-Day Periods)"
    )
    
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


    # Planting window advisory
    st.subheader("📅 Planting Window Advisory")
    st.caption("💡 **For farmers:** This tells you the best time to plant crops based on historical rainfall patterns.")

    st.success(
        f"**RECOMMENDED PLANTING PERIOD for {selected_zone}:** Based on past years, the best time to plant is between **March 15 and April 30**."
    )

    st.info(
        "**Why this period?** This is when rain usually starts and soil is warm enough for seeds to grow. Always check current year weather before planting!"
    )

# --- TAB 6: Data Archive ---
with tab6:
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


with tab5:
    # --- CROP PLANNING & SEASONAL RECOMMENDATIONS ---
    st.markdown("---")
    st.header("🗓️ Crop Planning & Seasonal Recommendations")
    
    st.info("👨‍🌾 **What This Shows:** Smart crop recommendations based on current season, historical weather patterns, and planting calendars. Tells you which crops to plant NOW for best results.")
    
    # Get current month and season
    current_month = datetime.now().month
    current_season = get_current_season(current_month)
    month_names = ["", "January", "February", "March", "April", "May", "June", 
                  "July", "August", "September", "October", "November", "December"]
    
    # Display current season
    col_season1, col_season2 = st.columns([1, 2])
    
    with col_season1:
        st.markdown(f"### 📅 Current Month")
        st.markdown(f"# {month_names[current_month]}")
        st.caption(f"Month {current_month} of 12")
    
    with col_season2:
        st.markdown(f"### 🌦️ Agricultural Season")
        st.markdown(f"# {current_season['name']}")
        st.write(f"**Characteristics:**")
        st.write(f"- Rainfall: {current_season['characteristics']['rainfall']}")
        st.write(f"- Temperature: {current_season['characteristics']['temperature']}")
        st.write(f"- Farming: {current_season['characteristics']['farming_activities']}")
    
    st.markdown("---")
    
    # Get crop recommendations
    with st.spinner("Analyzing historical data and calculating crop suitability..."):
        # Prepare historical data
        df_history = df_raw[df_raw["Zone"] == selected_zone].copy()
        
        # Get recommendations
        recommendations = get_crop_recommendations(df_history, current_month, selected_zone)
    
    # Display recommendations by category
    st.subheader("🌾 Recommended Crops for This Month")
    
    # Recommendations
    st.subheader("🌟 Top Recommendations")
    
    if st.button("🔊 Listen to Crop Recommendations"):
         top_crop = recommendations[0] if recommendations else None
         season = get_current_season()
         crop_text = generate_crop_plan_summary(top_crop, season)
         autoplay_audio(text_to_audio(crop_text))[0]
    
    # Group by category
    highly_recommended = [r for r in recommendations if r['priority'] == 1]
    recommended = [r for r in recommendations if r['priority'] == 2]
    moderately_suitable = [r for r in recommendations if r['priority'] == 3]
    not_recommended = [r for r in recommendations if r['priority'] == 4]
    
    # Highly Recommended
    if highly_recommended:
        st.markdown("### 🟢 HIGHLY RECOMMENDED (Plant Now!)")
        st.success("These crops are in their optimal planting window with ideal conditions expected.")
        
        for i, rec in enumerate(highly_recommended, 1):
            with st.expander(f"{i}. **{rec['crop']}** - {rec['score']:.0f}% Match", expanded=(i==1)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Why This Crop:**")
                    for reason in rec['reasons']:
                        st.write(f"- {reason}")
                
                with col2:
                    st.markdown("**Quick Facts:**")
                    st.write(f"💧 Water: {rec['water_requirement']}")
                    st.write(f"🌱 Soil: {rec['soil_type']}")
                    st.write(f"📅 Growing: {rec['growing_days']} days")
                    st.write(f"� Harvest: {rec['expected_harvest']}")
                    st.write(f"🗓️ Best Planting: {rec['optimal_planting_text']}")
                
                st.caption(f"ℹ️ {rec['description']}")
    
    # Recommended
    if recommended:
        st.markdown("### 🟡 RECOMMENDED (Good to Plant)")
        st.info("These crops can be planted now with good success potential.")
        
        for i, rec in enumerate(recommended, 1):
            with st.expander(f"{i}. **{rec['crop']}** - {rec['score']:.0f}% Match"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Analysis:**")
                    for reason in rec['reasons']:
                        st.write(f"- {reason}")
                
                with col2:
                    st.markdown("**Details:**")
                    st.write(f"💧 {rec['water_requirement']}")
                    st.write(f"🌱 {rec['soil_type']}")
                    st.write(f"📅 {rec['growing_days']} days")
                    st.write(f"� {rec['expected_harvest']}")
                    st.write(f"🗓️ Best Plant: {rec['optimal_planting_text']}")
    
    # Moderately Suitable
    if moderately_suitable:
        st.markdown("### 🟠 MODERATELY SUITABLE (Consider Carefully)")
        st.warning("These crops can work but may need extra care or have suboptimal conditions.")
        
        for i, rec in enumerate(moderately_suitable, 1):
            with st.expander(f"{i}. **{rec['crop']}** - {rec['score']:.0f}% Match"):
                for reason in rec['reasons']:
                    st.write(f"- {reason}")
                st.caption(f"Growing: {rec['growing_days']} days | Harvest: {rec['expected_harvest']} | Best Plant: {rec['optimal_planting_text']}")
    
    # Not Recommended
    if not_recommended:
        with st.expander("🔴 NOT RECOMMENDED (Wait for Better Season)", expanded=False):
            st.error("These crops are not suitable for planting this month. Wait for their optimal season.")
            
            for rec in not_recommended:
                st.write(f"**{rec['crop']}** ({rec['score']:.0f}%)")
                for reason in rec['reasons']:
                    st.write(f"  - {reason}")
                st.write("")
    
    st.markdown("---")
    
    # Planting Calendar Visualization
    st.subheader("📆 Annual Planting Calendar")
    st.caption("Visual guide showing optimal planting months for each crop throughout the year")
    
    # Create calendar heatmap
    calendar_data = get_planting_calendar()
    
    # Prepare data for heatmap
    crops = list(calendar_data.keys())
    months = list(range(1, 13))
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Create matrix: 2 = optimal, 1 = acceptable, 0 = not suitable
    calendar_matrix = []
    for crop in crops:
        row = []
        for month in months:
            if month in calendar_data[crop]['optimal']:
                row.append(2)  # Optimal
            elif month in calendar_data[crop]['planting']:
                row.append(1)  # Acceptable
            else:
                row.append(0)  # Not suitable
        calendar_matrix.append(row)
    
    # Create heatmap
    fig_calendar = go.Figure(data=go.Heatmap(
        z=calendar_matrix,
        x=month_labels,
        y=crops,
        colorscale=[
            [0, '#2d2d2d'],      # Not suitable - dark gray
            [0.5, '#FFA726'],    # Acceptable - orange
            [1, '#66BB6A']       # Optimal - green
        ],
        showscale=False,
        hovertemplate='<b>%{y}</b><br>Month: %{x}<br>Status: %{z}<extra></extra>',
        text=[[
            'Optimal' if calendar_matrix[i][j] == 2 
            else 'Acceptable' if calendar_matrix[i][j] == 1 
            else 'Not Suitable' 
            for j in range(12)
        ] for i in range(len(crops))],
        texttemplate='',
    ))
    
    # Highlight current month
    fig_calendar.add_vline(
        x=current_month - 1,
        line_dash="dash",
        line_color="cyan",
        line_width=3,
        annotation_text=f"Current: {month_labels[current_month-1]}",
        annotation_position="top"
    )
    
    fig_calendar.update_layout(
        title="Crop Planting Calendar - Abia State",
        xaxis_title="Month",
        yaxis_title="Crop",
        height=500,
        xaxis=dict(side='top'),
    )
    
    st.plotly_chart(fig_calendar, use_container_width=True)
    
    # Legend
    col_leg1, col_leg2, col_leg3 = st.columns(3)
    with col_leg1:
        st.markdown("🟢 **Green** = Optimal planting window")
    with col_leg2:
        st.markdown("🟠 **Orange** = Acceptable planting period")
    with col_leg3:
        st.markdown("⬛ **Gray** = Not recommended")
    
    st.caption("💡 **Tip:** Focus on crops showing green (optimal) for current month for best results!")
    
    st.markdown("---")
    
    # --- Integrated GDD Tracking Section ---
    st.subheader("🌱 Track Crop Progress (GDD)")
    st.info("👨‍🌾 **Monitor Your Crops:** Select a crop below to track its growth progress based on heat accumulation (Growing Degree Days).")
    
    with st.expander("❓ What is GDD? (Click to learn more)"):
        st.write("""
        **Growing Degree Days (GDD)** measures the heat your crops receive.
        - **How it works:** We add up daily heat units. When the total reaches the target, the crop is ready.
        - **Why use it:** It's more accurate than counting calendar days because crops grow faster in warm weather.
        """)
    
    # Crop Selector using dynamic database
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        crop_track_name = st.selectbox(
            "Select Crop to Track:", 
            list(SEASONAL_CROPS.keys()),
            key="gdd_crop_select"
        )
    
    # Get parameters from SEASONAL_CROPS
    crop_params = SEASONAL_CROPS[crop_track_name]
    t_base_track = crop_params["T_base"]
    gdd_target_track = crop_params["GDD_to_Maturity"] # Total Required
    
    with col_sel2:
        # Planting Date Input (Defaults to 30 days ago for demo)
        default_plant = datetime.now() - timedelta(days=30)
        planting_date = st.date_input(
            "Select Planting Date:",
            value=default_plant,
            key="gdd_plant_date",
            help="Select the date when the crop was planted to track progress accurately."
        )

    col_track1, col_track2 = st.columns(2)
    with col_track1:
        st.write(f"**Crop:** {crop_track_name}")
        st.write(f"**Base Temp:** {t_base_track}°C")
    with col_track2:
        st.write(f"**Maturity Target:** {gdd_target_track} GDD")
        st.write(f"**Growing Season:** {crop_params['growing_season_days']} days (approx)")
    
    # Filter history for this crop season (from planting date)
    # Ensure specific date comparison
    plant_ts = pd.Timestamp(planting_date)
    if df_history.index.tz is not None and plant_ts.tz is None:
         plant_ts = plant_ts.tz_localize(df_history.index.tz)
    elif df_history.index.tz is None and plant_ts.tz is not None:
         plant_ts = plant_ts.tz_localize(None)

    df_crop_season = df_history[df_history.index >= plant_ts].copy()
    
    if df_crop_season.empty:
         st.warning("No data available since selected planting date.")
    else:
        # Calculate GDD for this specific season
        df_gdd_track = calculate_gdd(df_crop_season, t_base_track) 
        
        if not df_gdd_track.empty:
            current_gdd_track = df_gdd_track["Cumulative_GDD"].iloc[-1]
            
            # Calculate progress
            progress_track = (current_gdd_track / gdd_target_track) * 100
            
            # Metrics
            # User request: "Cumulative, current and total GDD"
            # We interpret: Cumulative = Total so far, Total = Target, Current = Daily Avg?
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Cumulative GDD", f"{current_gdd_track:.0f}", help="Total heat units accumulated since planting")
            m2.metric("Required Total", f"{gdd_target_track}", help="Total GDD needed for maturity")
            
            # Current Daily GDD (Average of last 7 days)
            recent_daily_gdd = df_gdd_track.tail(7)["Daily_GDD"].mean()
            m3.metric("Daily GDD (Avg)", f"{recent_daily_gdd:.1f}", help="Average GDD gained per day recently")
            
            m4.metric("Progress", f"{progress_track:.1f}%")
            
            # Progress Bar
            st.progress(min(progress_track / 100, 1.0))
            
            # Status Message
            if progress_track >= 100:
                st.success(f"🎉 **Ready for Harvest!** {crop_track_name} has reached maturity.")
            elif progress_track >= 80:
                st.info("🌾 **Almost Ready.** Crop is nearing maturity.")
            elif progress_track >= 50:
                st.info("✅ **Good Progress.** Halfway there!")
            else:
                st.info("🌱 **Growing.** Early development stage.")
                
            # Estimated Dates
            if progress_track < 100 and recent_daily_gdd > 0:
                # Remaining GDD
                remaining_gdd = gdd_target_track - current_gdd_track
                days_remaining = max(0, remaining_gdd / recent_daily_gdd)
                est_harvest = datetime.now() + timedelta(days=int(days_remaining))
                
                st.markdown(f"### 🗓️ Estimated Harvest: **{est_harvest.strftime('%B %d, %Y')}**")
                st.caption(f"Based on recent weather, you have approx. **{int(days_remaining)} days** left to reach maturity.")
        
            # Chart
            fig_track = px.line(
                df_gdd_track.reset_index(), # Show all data from planting
                x="Timestamp",
                y="Cumulative_GDD",
                title=f"GDD Accumulation Since Planting ({planting_date})",
                labels={"Cumulative_GDD": "Accumulated Heat units"}
            )
            fig_track.add_hline(y=gdd_target_track, line_dash="dash", line_color="green", annotation_text="Target")
            st.plotly_chart(fig_track, use_container_width=True)
    
    
