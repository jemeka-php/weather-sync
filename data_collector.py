# data_collector.py - Enhanced with Logging, Error Handling, and Robustness

import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import schedule
from typing import Dict, List, Optional
import sys
try:
    from supabase import create_client, Client
except ImportError:
    Client = None
    create_client = None

from config import (
    API_KEY,
    AGRICULTURAL_ZONES,
    WEATHER_API_URL,
    DATA_ARCHIVE_FILE,
    BACKUP_DIR,
    API_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
    LOG_FILE,
    LOG_LEVEL,
    LOG_FILE,
    LOG_LEVEL,
    DATA_RETENTION_DAYS,
    SUPABASE_URL,
    SUPABASE_KEY,
)

# --- Logging Configuration ---
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class WeatherDataCollector:
    """Enhanced weather data collector with retry logic and error handling."""

    def __init__(self):
        self.api_key = API_KEY
        self.zones = AGRICULTURAL_ZONES
        self.archive_file = DATA_ARCHIVE_FILE
        
        # Initialize Supabase Client
        self.supabase: Optional[Client] = None
        if SUPABASE_URL and SUPABASE_KEY and create_client:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")

    def fetch_weather_data(self, zone: str, coords: Dict) -> Optional[Dict]:
        """
        Fetch weather data for a specific zone with retry logic.

        Args:
            zone: Name of the agricultural zone
            coords: Dictionary containing lat, lon coordinates

        Returns:
            Dictionary with weather data or None if failed
        """
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": self.api_key,
            "units": "metric",
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(
                    WEATHER_API_URL, params=params, timeout=API_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()

                # Extract and structure the data
                rain_1h = data.get("rain", {}).get("1h", 0.0)
                rain_3h = data.get("rain", {}).get("3h", 0.0)

                record = {
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Zone": zone,
                    "T_current": data["main"]["temp"],
                    "T_min": data["main"].get("temp_min", data["main"]["temp"]),
                    "T_max": data["main"].get("temp_max", data["main"]["temp"]),
                    "Feels_Like": data["main"].get("feels_like", data["main"]["temp"]),
                    "Humidity": data["main"]["humidity"],
                    "Pressure": data["main"]["pressure"],
                    "Wind_Speed": data.get("wind", {}).get("speed", 0.0),
                    "Wind_Direction": data.get("wind", {}).get("deg", 0),
                    "Cloudiness": data.get("clouds", {}).get("all", 0),
                    "Precipitation_1h": rain_1h,
                    "Precipitation_3h": rain_3h,
                    "Weather_Condition": data.get("weather", [{}])[0].get(
                        "main", "Unknown"
                    ),
                    "Weather_Description": data.get("weather", [{}])[0].get(
                        "description", "Unknown"
                    ),
                    "Visibility": data.get("visibility", 0) / 1000,  # Convert to km
                }

                logger.info(f"Successfully fetched data for {zone}")
                return record

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.error(f"Invalid API key. Please check your credentials.")
                    return None
                elif e.response.status_code == 404:
                    logger.error(f"Location not found for {zone}")
                    return None
                else:
                    logger.warning(
                        f"HTTP error for {zone} (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                    )

            except requests.exceptions.Timeout:
                logger.warning(
                    f"Timeout for {zone} (attempt {attempt + 1}/{MAX_RETRIES})"
                )

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Request error for {zone} (attempt {attempt + 1}/{MAX_RETRIES}): {e}"
                )

            except Exception as e:
                logger.error(f"Unexpected error for {zone}: {e}", exc_info=True)
                return None

            # Wait before retrying
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

        logger.error(f"Failed to fetch data for {zone} after {MAX_RETRIES} attempts")
        return None

    def store_data(self, records: List[Dict]) -> bool:
        """
        Store collected weather data to CSV archive.

        Args:
            records: List of weather data dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not records:
            logger.warning("No records to store")
            return False

        try:
            new_df = pd.DataFrame(records)

            # Load existing archive or create new one
            if self.archive_file.exists():
                archive_df = pd.read_csv(self.archive_file)
                combined_df = pd.concat([archive_df, new_df], ignore_index=True)
            else:
                combined_df = new_df
                logger.info("Creating new archive file")

            # Remove duplicates based on Timestamp and Zone
            combined_df.drop_duplicates(
                subset=["Timestamp", "Zone"], keep="last", inplace=True
            )

            # Save to archive
            combined_df.to_csv(self.archive_file, index=False)
            logger.info(f"Successfully stored {len(records)} new records")

            # Perform data cleanup
            self.cleanup_old_data(combined_df)

            # Push to Supabase (Non-blocking ideally, but sequential for simplicity)
            if self.supabase:
                self.store_to_supabase(records)

            return True

        except Exception as e:
            return False

    def store_to_supabase(self, records: List[Dict]) -> None:
        """Push records to Supabase."""
        try:
            # Prepare records for Supabase (ensure keys match DB columns if needed)
            # Assuming DB columns match dictionary keys (snake_case vs PascalCase might be an issue)
            # Users CSV used Title Case keys (e.g. 'T_current'). Supabase usually likes snake_case.
            # I will assume the user created the table with columns matching the CSV headers or I should map them.
            # To be safe, I will stick to what we have or try to map if I knew the schema.
            # Given the user just "created the table", I'll assume they might have used the CSV columns or standard snake_case.
            # For now, I'll convert keys to lowercase snake_case which is standard for PG.
            
            supabase_records = []
            for r in records:
                new_r = {}
                for k, v in r.items():
                    # specific mappings if needed, else simple lowercase
                    # e.g. T_current -> t_current
                    new_r[k.lower()] = v
                supabase_records.append(new_r)

            response = self.supabase.table("weather_data").insert(supabase_records).execute()
            logger.info(f"Successfully pushed {len(records)} records to Supabase")
        except Exception as e:
            logger.error(f"Error pushing to Supabase: {e}")

    def cleanup_old_data(self, df: pd.DataFrame) -> None:
        """Remove data older than DATA_RETENTION_DAYS."""
        try:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"])
            cutoff_date = datetime.now() - timedelta(days=DATA_RETENTION_DAYS)

            original_count = len(df)
            df_cleaned = df[df["Timestamp"] >= cutoff_date]
            removed_count = original_count - len(df_cleaned)

            if removed_count > 0:
                df_cleaned.to_csv(self.archive_file, index=False)
                logger.info(f"Removed {removed_count} old records")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def create_backup(self) -> None:
        """Create a backup of the current data archive."""
        try:
            if self.archive_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = BACKUP_DIR / f"backup_{timestamp}.csv"

                df = pd.read_csv(self.archive_file)
                df.to_csv(backup_file, index=False)

                logger.info(f"Backup created: {backup_file}")

                # Keep only last 10 backups
                backups = sorted(BACKUP_DIR.glob("backup_*.csv"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()
                        logger.info(f"Removed old backup: {old_backup}")

        except Exception as e:
            logger.error(f"Error creating backup: {e}")

    def fetch_and_store_weather(self) -> bool:
        """Main function to fetch and store weather data for all zones."""
        logger.info("=" * 60)
        logger.info(f"Starting data collection at {datetime.now()}")
        logger.info("=" * 60)

        all_records = []

        for zone, coords in self.zones.items():
            record = self.fetch_weather_data(zone, coords)
            if record:
                all_records.append(record)
            time.sleep(1)  # Be respectful to API rate limits

        success = self.store_data(all_records)

        if success:
            logger.info(f"Data collection completed successfully")
            return True
        else:
            logger.warning(f"Data collection completed with errors")
            return False

        logger.info("=" * 60)


def run_scheduler():
    """Run the scheduled data collection."""
    collector = WeatherDataCollector()

    # Run immediately on startup
    collector.fetch_and_store_weather()

    # Create initial backup
    collector.create_backup()

    # Schedule regular collection (every 3 hours)
    schedule.every(3).hours.do(collector.fetch_and_store_weather)

    # Schedule daily backup (at 2 AM)
    schedule.every().day.at("02:00").do(collector.create_backup)

    logger.info("Scheduler started. Press Ctrl+C to stop.")

    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")


if __name__ == "__main__":
    try:
        if "--run-once" in sys.argv:
            # Run one-off collection (useful for cron jobs/GitHub Actions)
            collector = WeatherDataCollector()
            # Fetch data and exit with 0 if success, 1 if failure
            success = collector.fetch_and_store_weather()
            if not success:
               logger.error("Run-once collection failed")
               sys.exit(1)
        else:
            # Run as long-running scheduler
            run_scheduler()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
