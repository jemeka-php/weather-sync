import pandas as pd
import numpy as np
from datetime import datetime

def generate_overview_summary(zone, latest, stats):
    """Generates a summary for the Overview & Trends section."""
    if not isinstance(latest, pd.Series) or not stats:
        return "Data unavailable for overview."

    temp = latest.get('T_current', 0)
    humidity = latest.get('Humidity', 0)
    rain = latest.get('Precipitation_1h', 0)
    
    text = f"Overview for {zone}. The current temperature is {temp:.1f} degrees Celsius with {humidity:.0f} percent humidity. "
    
    if rain > 0:
        text += f"It is currently raining, with {rain:.1f} millimeters in the last hour. "
    else:
        text += "It is currently dry. "
        
    text += f"The average temperature recently has been {stats.get('avg_temp', 0):.1f} degrees. "
    text += f"Total rainfall in the last 30 days is {stats.get('total_rain_30d', 0):.1f} millimeters."
    return text

def generate_temp_trend_summary(df_zone):
    """Generates summary for Temperature Trends."""
    if df_zone.empty:
        return "No temperature trend data available."
    
    recent = df_zone.tail(24)
    max_t = recent['T_max'].max()
    min_t = recent['T_min'].min()
    
    text = f"In the last 24 hours, temperatures ranged from a low of {min_t:.1f} to a high of {max_t:.1f} degrees. "
    
    # Simple trend detection
    start_temp = recent['T_current'].iloc[0]
    end_temp = recent['T_current'].iloc[-1]
    diff = end_temp - start_temp
    
    if diff > 2:
        text += "The temperature is generally rising."
    elif diff < -2:
        text += "The temperature is generally falling."
    else:
        text += "The temperature has been relatively stable."
        
    return text

def generate_wind_summary(df_zone):
    """Generates summary for Wind & Atmosphere."""
    if df_zone.empty:
        return "No wind data available."
        
    latest = df_zone.iloc[-1]
    speed = latest.get('Wind_Speed', 0)
    pressure = latest.get('Pressure', 0)
    
    text = f"Current wind speed is {speed:.1f} meters per second. Atmospheric pressure is {pressure:.0f} hectopascals. "
    
    if speed > 5:
        text += "It is quite windy. "
    else:
        text += "Winds are calm. "
        
    return text

def generate_hourly_forecast_summary(df_hourly):
    """Generates summary for next 24h forecast."""
    if df_hourly.empty:
        return "Forecast unavailable."
        
    next_24 = df_hourly.head(8)
    avg_temp = next_24['temp'].mean()
    max_pop = next_24['pop'].max()
    
    text = f"Forecast for the next 24 hours. Expect an average temperature of {avg_temp:.1f} degrees. "
    
    if max_pop > 50:
        text += f"There is a high chance of rain, up to {max_pop:.0f} percent. Plan accordingly."
    else:
        text += "Rain is unlikely in the next 24 hours."
        
    return text

def generate_daily_forecast_summary(df_daily):
    """Generates summary for 5-day forecast."""
    if df_daily.empty:
        return "Daily forecast unavailable."
        
    text = "Five day forecast. "
    for _, row in df_daily.head(3).iterrows():
        day = row['date'].strftime("%A")
        cond = row['weather']
        high = row['temp_max']
        text += f"{day} will be {cond}, with a high of {high:.0f}. "
        
    return text

def generate_historical_rain_summary(monthly_rain_df):
    """Generates summary for historical rainfall."""
    if monthly_rain_df is None or monthly_rain_df.empty:
        return "Historical rainfall data unavailable."
        
    last_month = monthly_rain_df.iloc[-1]
    month_name = last_month['Date'].strftime("%B")
    amount = last_month['Rainfall']
    
    text = f"Rainfall Analysis. In {month_name}, we recorded {amount:.1f} millimeters of rain. "
    
    if len(monthly_rain_df) > 12:
        prev_year = monthly_rain_df.iloc[-13]
        text += f"Compared to last year, this is {'more' if amount > prev_year['Rainfall'] else 'less'} rain."
        
    return text

def generate_drought_risk_summary(latest_risk):
    current_status = latest_risk.get("Risk_Flag", "Normal")
    rain_7d = latest_risk.get("Rain_7D_Sum", 0)
    
    text = f"Risk Analysis. Current status is {current_status}. "
    text += f"We have had {rain_7d:.1f} millimeters of rain in the last 7 days. "
    
    if current_status == "Drought Risk":
        text += "Crops may be water stressed. Irrigation is recommended."
    elif current_status == "Waterlogging Risk":
        text += "Excess water detected. Ensure good drainage."
        
    return text

def generate_crop_plan_summary(top_crop, season):
    if not top_crop:
        return "No crop recommendations available."
        
    text = f"Crop Planning. It is currently the {season} season. "
    text += f"The best crop to plant now is {top_crop['crop']}. {top_crop['description']}"
    return text
