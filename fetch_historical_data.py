import requests
import pandas as pd
import time
import sys
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config import AGRICULTURAL_ZONES, DATA_ARCHIVE_FILE, SUPABASE_URL, SUPABASE_KEY

try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None

# Constants
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
END_DATE = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def fetch_historical_data(zone_name, lat, lon):
    """Fetch historical data for a specific zone."""
    print(f"Fetching data for {zone_name} from {START_DATE} to {END_DATE}...", flush=True)
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": "temperature_2m,relative_humidity_2m,rain,surface_pressure,cloud_cover,wind_speed_10m,wind_direction_10m",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(ARCHIVE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get("hourly", {})
        
        if not hourly:
            print(f"Warning: No hourly data found for {zone_name}", flush=True)
            return pd.DataFrame()

        # Create Initial DataFrame (Extract)
        df = pd.DataFrame({
            "Timestamp": pd.to_datetime(hourly["time"]),
            "Zone": zone_name,
            "T_current": hourly["temperature_2m"],
            "T_min": hourly["temperature_2m"], # Approximation for hourly
            "T_max": hourly["temperature_2m"], # Approximation for hourly
            "Feels_Like": hourly["temperature_2m"], # Approximation
            "Humidity": hourly["relative_humidity_2m"],
            "Pressure": hourly["surface_pressure"],
            "Wind_Speed": hourly["wind_speed_10m"],
            "Wind_Direction": hourly["wind_direction_10m"],
            "Cloudiness": hourly["cloud_cover"],
            "Precipitation_1h": hourly["rain"],
            "Precipitation_3h": 0.0, 
            "Weather_Condition": "Unknown",
            "Weather_Description": "Historical Data",
            "Visibility": 10.0
        })

        # --- Transform & Clean (ETL Phase) ---
        df = clean_and_transform_data(df)
        
        print(f"  -> Fetched & Cleaned {len(df)} records for {zone_name}", flush=True)
        return df
    
    except Exception as e:
        print(f"Error fetching data for {zone_name}: {e}", flush=True)
        return pd.DataFrame()

def clean_and_transform_data(df):
    """
    Robust ETL Cleaning function.
    - Interpolates missing values.
    - Caps outliers to physical limits.
    - Ensures consistency.
    """
    if df.empty:
        return df

    # 1. Deduplication
    df.drop_duplicates(subset=["Timestamp"], keep="last", inplace=True)

    # 2. Resampling & Filling (Handling Gaps)
    # Ensure a complete hourly index
    df = df.set_index("Timestamp").sort_index()
    # Reindex to full range to find gaps
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq="H")
    df = df.reindex(full_range)
    
    # Forward fill non-numeric static columns (Zone)
    df["Zone"] = df["Zone"].ffill().bfill()
    df["Weather_Condition"] = df["Weather_Condition"].fillna("Unknown")
    df["Weather_Description"] = df["Weather_Description"].fillna("Interpolated")

    # Interpolate numeric linear data (Temp, Pressure)
    numeric_cols = ["T_current", "T_min", "T_max", "Feels_Like", "Pressure", "Visibility"]
    for col in numeric_cols:
         if col in df.columns:
             df[col] = df[col].interpolate(method="linear", limit=24) # Limit interpolation to 24h gaps

    # Safe fill for variable data (Rain, Wind) - Interpolation might create rain where there is none?
    # Wind/Humidity typically usually safe to interpolate linearly for short gaps
    df["Humidity"] = df["Humidity"].interpolate(method="linear", limit=24)
    df["Wind_Speed"] = df["Wind_Speed"].interpolate(method="linear", limit=24)
    df["Cloudiness"] = df["Cloudiness"].interpolate(method="linear", limit=24)
    
    # Rain: fill gaps with 0.0 (Conservative assumption)
    df["Precipitation_1h"] = df["Precipitation_1h"].fillna(0.0)
    df["Precipitation_3h"] = df["Precipitation_3h"].fillna(0.0)

    # 3. Outlier Handling & Physical Consistency
    # Humidity 0-100
    if "Humidity" in df.columns:
        df["Humidity"] = df["Humidity"].clip(lower=0.0, upper=100.0)
    
    # Cloudiness 0-100
    if "Cloudiness" in df.columns:
        df["Cloudiness"] = df["Cloudiness"].clip(lower=0.0, upper=100.0)

    # Negative Rain -> 0
    if "Precipitation_1h" in df.columns:
        df["Precipitation_1h"] = df["Precipitation_1h"].clip(lower=0.0)

    # Reset index to get Timestamp back as column
    df.index.name = "Timestamp"
    df = df.reset_index()
    
    return df

def main():
    print("Starting historical data fetch...", flush=True)
    all_data = []
    
    for zone, coords in AGRICULTURAL_ZONES.items():
        df_zone = fetch_historical_data(zone, coords["lat"], coords["lon"])
        if not df_zone.empty:
            all_data.append(df_zone)
        time.sleep(2) # Rate limiting
        
    if all_data:
        print("Combining data...", flush=True)
        new_historical_df = pd.concat(all_data, ignore_index=True)
        
        # Load existing data if available
        if DATA_ARCHIVE_FILE.exists():
            print(f"Loading existing archive from {DATA_ARCHIVE_FILE}...", flush=True)
            try:
                existing_df = pd.read_csv(DATA_ARCHIVE_FILE)
                existing_df["Timestamp"] = pd.to_datetime(existing_df["Timestamp"])
                
                # Combine and deduplicate
                combined_df = pd.concat([existing_df, new_historical_df], ignore_index=True)
                combined_df.drop_duplicates(subset=["Timestamp", "Zone"], keep="last", inplace=True)
            except Exception as e:
                print(f"Error reading existing archive: {e}. Overwriting...", flush=True)
                combined_df = new_historical_df
        else:
            print("Creating new archive...", flush=True)
            combined_df = new_historical_df
            
        # Sort
        combined_df.sort_values(by=["Zone", "Timestamp"], inplace=True)
        
        # Save
        combined_df.to_csv(DATA_ARCHIVE_FILE, index=False)
        print(f"Successfully saved {len(combined_df)} records to {DATA_ARCHIVE_FILE}", flush=True)
        
        # --- Push to Supabase ---
        if SUPABASE_URL and SUPABASE_KEY and create_client:
            print("Syncing with Supabase...", flush=True)
            try:
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                
                # Convert DataFrame to records
                # Supabase likely expects lowercase keys if created automatically or snake_case
                # Adapting keys to match what data_collector uses (lowercase)
                
                # Convert timestamps to string for JSON serialization
                temp_df = combined_df.copy()
                temp_df["Timestamp"] = temp_df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
                # Fix: Supabase Pressure column seems to be Integer, but API returns Float
                temp_df["Pressure"] = temp_df["Pressure"].round().astype(int)
                
                records = temp_df.to_dict(orient="records")
                
                # Batch insert to avoid payload limits
                batch_size = 1000
                total_records = len(records)
                print(f"Pushing {total_records} records in batches of {batch_size}...", flush=True)
                
                for i in range(0, total_records, batch_size):
                    batch = records[i:i+batch_size]
                    
                    # Transform keys to match expected DB schema (lowercase)
                    cleaned_batch = []
                    for r in batch:
                        new_r = {}
                        for k, v in r.items():
                            new_r[k.lower()] = v
                            # Handle NaNs which JSON doesn't like
                            if pd.isna(v):
                                new_r[k.lower()] = None
                        cleaned_batch.append(new_r)
                        
                    try:
                        # Use upsert to handle duplicates if primary key is set (e.g. timestamp + zone)
                        # Assuming table is 'weather_data'
                        supabase.table("weather_data").upsert(cleaned_batch).execute()
                        print(f"  -> Uploaded batch {i//batch_size + 1}/{(total_records + batch_size - 1)//batch_size}", flush=True)
                    except Exception as e:
                        print(f"  -> Error uploading batch {i}: {e}", flush=True)
                        
                print("Supabase sync complete!", flush=True)
                
            except Exception as e:
                print(f"Failed to initialize Supabase sync: {e}", flush=True)
    else:
        print("No data fetched.", flush=True)

if __name__ == "__main__":
    main()
