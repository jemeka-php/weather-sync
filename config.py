# config.py - Enhanced Configuration with Security and Validation

import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Security: Load API Key from Environment Variable ---
# This prevents hardcoding sensitive credentials in source code
API_KEY = os.getenv("OPENWEATHER_API_KEY", "411a686a21f617a1d849b7ab15c352d9")

if not API_KEY:
    raise ValueError(
        "OPENWEATHER_API_KEY environment variable not set. "
        "Please set it using: export OPENWEATHER_API_KEY='your_key_here'"
    )

# --- Supabase Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Warning instead of Error for now, to allow partial functionality
    print("⚠️ Supabase credentials not found. Falling back to local CSV storage.")

def init_supabase():
    """Initialize and return the Supabase client."""
    from supabase import create_client, Client
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Failed to initialize Supabase: {e}")
        return None

# --- SMS Configuration (Termii) ---
TERMII_API_KEY = os.getenv("TERMII_API_KEY")
TERMII_SENDER_ID = os.getenv("TERMII_SENDER_ID", "N-Alert") # Default or requested Sender ID
TERMII_BASE_URL = "https://api.ng.termii.com/api"
TERMII_BASE_URL = "https://api.ng.termii.com/api"

# --- Email Configuration (SMTP) ---
# --- Email Configuration (SMTP) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- Agricultural Zones Configuration ---
# Coordinates are crucial for API calls
AGRICULTURAL_ZONES = {
    "Aba": {"lat": 5.1167, "lon": 7.3667, "elevation": 122},
    "Umuahia": {"lat": 5.5167, "lon": 7.4833, "elevation": 122},
    "Bende": {"lat": 5.6190, "lon": 7.6430, "elevation": 150},
}

# --- API Configuration ---
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "https://api.openweathermap.org/data/2.5/forecast"

# API request configuration
API_TIMEOUT = 10  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# --- Data Storage Configuration ---
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)  # Create data directory if it doesn't exist

DATA_ARCHIVE_FILE = DATA_DIR / "abia_weather_archive.csv"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# --- Crop Profiles Database ---
# Enhanced with more detailed agronomic parameters
CROP_PROFILES = {
    "Maize (Corn)": {
        "T_base": 10.0,
        "T_optimal_min": 20.0,
        "T_optimal_max": 30.0,
        "Rain_Annual_Min": 600,
        "Rain_Annual_Max": 900,
        "GDD_to_Maturity": 1200,
        "Growing_Season_Days": 90,
    },
    "Cassava": {
        "T_base": 18.0,
        "T_optimal_min": 25.0,
        "T_optimal_max": 29.0,
        "Rain_Annual_Min": 1000,
        "Rain_Annual_Max": 1500,
        "GDD_to_Maturity": 3000,
        "Growing_Season_Days": 240,
    },
    "Yam": {
        "T_base": 20.0,
        "T_optimal_min": 25.0,
        "T_optimal_max": 30.0,
        "Rain_Annual_Min": 1500,
        "Rain_Annual_Max": 2500,
        "GDD_to_Maturity": 2500,
        "Growing_Season_Days": 210,
    },
    "Rice": {
        "T_base": 12.0,
        "T_optimal_min": 22.0,
        "T_optimal_max": 32.0,
        "Rain_Annual_Min": 1200,
        "Rain_Annual_Max": 2000,
        "GDD_to_Maturity": 1800,
        "Growing_Season_Days": 120,
    },
    "Cowpea": {
        "T_base": 8.0,
        "T_optimal_min": 21.0,
        "T_optimal_max": 30.0,
        "Rain_Annual_Min": 500,
        "Rain_Annual_Max": 1200,
        "GDD_to_Maturity": 900,
        "Growing_Season_Days": 75,
    },
}

# --- Risk Thresholds ---
# Drought and waterlogging risk parameters
DROUGHT_THRESHOLD = 5.0  # 7-day sum <= 5.0 mm
WET_THRESHOLD = 150.0  # 7-day sum >= 150.0 mm
EXTREME_TEMP_HIGH = 38.0  # Celsius
EXTREME_TEMP_LOW = 10.0  # Celsius
CRITICAL_HUMIDITY_LOW = 30  # Percentage
CRITICAL_HUMIDITY_HIGH = 95  # Percentage

# --- Data Collection Schedule ---
COLLECTION_INTERVAL_HOURS = 3
DATA_RETENTION_DAYS = 730  # Keep 2 years of data

# --- Logging Configuration ---
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "weather_collector.log"
LOG_LEVEL = "INFO"

# --- Validation Functions ---
def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude values."""
    return -90 <= lat <= 90 and -180 <= lon <= 180

def validate_zones() -> bool:
    """Validate all configured zones."""
    for zone, coords in AGRICULTURAL_ZONES.items():
        if not validate_coordinates(coords["lat"], coords["lon"]):
            raise ValueError(f"Invalid coordinates for zone {zone}")
    return True

# Run validation on import
validate_zones()
