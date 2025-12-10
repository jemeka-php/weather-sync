# crop_recommender.py
"""
Intelligent Crop Recommendation System for Abia State
Analyzes historical weather data and current conditions to recommend optimal crops
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from seasonal_crops import SEASONAL_CROPS, get_current_season, is_planting_season


def calculate_crop_score(crop_name, crop_data, current_month, historical_data, current_conditions=None):
    """
    Calculate suitability score for a crop based on multiple factors
    
    Args:
        crop_name: Name of the crop
        crop_data: Crop information from SEASONAL_CROPS
        current_month: Current month (1-12)
        historical_data: DataFrame with historical weather data
        current_conditions: Optional dict with current weather conditions
    
    Returns:
        tuple: (score, reasons, category)
    """
    score = 0
    reasons = []
    
    # 1. PLANTING WINDOW ANALYSIS (40% weight)
    is_plantable, is_optimal, planting_reason = is_planting_season(crop_name, current_month)
    
    if is_optimal:
        score += 40
        reasons.append(f"✅ **Optimal planting window** - Peak season for {crop_name}")
    elif is_plantable:
        score += 25
        reasons.append(f"⚠️ **Acceptable planting period** - Can plant but not peak season")
    else:
        score += 0
        reasons.append(f"❌ **Wrong season** - {planting_reason}")
    
    # 2. TEMPERATURE MATCH (30% weight)
    if not historical_data.empty:
        # Get average temperature for this month from historical data
        historical_data['month'] = historical_data.index.month
        monthly_temps = historical_data[historical_data['month'] == current_month]
        
        if not monthly_temps.empty and 'T_avg' in monthly_temps.columns:
            avg_temp = monthly_temps['T_avg'].mean()
            min_temp_req, max_temp_req = crop_data['optimal_temp_range']
            
            if min_temp_req <= avg_temp <= max_temp_req:
                score += 30
                reasons.append(f"✅ **Temperature ideal** ({avg_temp:.1f}°C suits {min_temp_req}-{max_temp_req}°C range)")
            elif min_temp_req - 3 <= avg_temp <= max_temp_req + 3:
                score += 20
                reasons.append(f"⚠️ **Temperature acceptable** ({avg_temp:.1f}°C near {min_temp_req}-{max_temp_req}°C range)")
            else:
                score += 5
                reasons.append(f"❌ **Temperature suboptimal** ({avg_temp:.1f}°C outside {min_temp_req}-{max_temp_req}°C range)")
        else:
            score += 15  # Neutral score if no data
            reasons.append("ℹ️ Temperature data unavailable for analysis")
    
    # 3. RAINFALL ADEQUACY (20% weight)
    if not historical_data.empty:
        # Get expected rainfall for the growing season
        planting_months = crop_data['planting_months']
        growing_days = crop_data['growing_season_days']
        
        # Estimate harvest month
        harvest_month = (current_month + (growing_days // 30)) % 12
        if harvest_month == 0:
            harvest_month = 12
        
        # Get rainfall for growing period
        season_months = []
        for i in range(growing_days // 30 + 1):
            month = (current_month + i - 1) % 12 + 1
            season_months.append(month)
        
        seasonal_rain = historical_data[historical_data['month'].isin(season_months)]
        
        if not seasonal_rain.empty and 'Daily_Precipitation' in seasonal_rain.columns:
            expected_rainfall = seasonal_rain['Daily_Precipitation'].sum() / len(seasonal_rain['month'].unique())
            min_rain, max_rain = crop_data['rainfall_annual_mm']
            
            # Adjust for growing season length
            season_min = (min_rain / 365) * growing_days
            season_max = (max_rain / 365) * growing_days
            
            if season_min <= expected_rainfall <= season_max:
                score += 20
                reasons.append(f"✅ **Adequate rainfall expected** ({expected_rainfall:.0f}mm for growing season)")
            elif expected_rainfall < season_min:
                deficit = season_min - expected_rainfall
                if crop_data['water_requirement'] == "Low":
                    score += 15
                    reasons.append(f"⚠️ **Below optimal rain** but crop is drought-tolerant")
                else:
                    score += 5
                    reasons.append(f"❌ **Insufficient rainfall** ({deficit:.0f}mm below minimum, irrigation needed)")
            else:  # Too much rain
                if crop_data['water_requirement'] in ["High", "Very High"]:
                    score += 18
                    reasons.append(f"✅ **High rainfall suits water-loving crop**")
                else:
                    score += 10
                    reasons.append(f"⚠️ **Heavy rainfall expected** - ensure good drainage")
        else:
            score += 10  # Neutral score
            reasons.append("ℹ️ Rainfall data unavailable for analysis")
    
    # 4. HISTORICAL SUCCESS RATE (10% weight)
    # Based on how many years had successful conditions
    if not historical_data.empty:
        success_years = 0
        total_years = len(historical_data.index.year.unique())
        
        for year in historical_data.index.year.unique():
            year_data = historical_data[historical_data.index.year == year]
            year_data_month = year_data[year_data['month'] == current_month]
            
            if not year_data_month.empty and 'T_avg' in year_data_month.columns:
                year_temp = year_data_month['T_avg'].mean()
                min_temp, max_temp = crop_data['optimal_temp_range']
                
                if min_temp <= year_temp <= max_temp:
                    success_years += 1
        
        if total_years > 0:
            success_rate = (success_years / total_years) * 100
            score += (success_rate / 100) * 10
            reasons.append(f"📊 **Historical success:** {success_rate:.0f}% of years had suitable conditions")
        else:
            score += 5
            reasons.append("ℹ️ Insufficient historical data for success rate")
    
    # Determine category based on final score
    if score >= 85:
        category = "🟢 HIGHLY RECOMMENDED"
        priority = 1
    elif score >= 70:
        category = "🟡 RECOMMENDED"
        priority = 2
    elif score >= 50:
        category = "🟠 MODERATELY SUITABLE"
        priority = 3
    else:
        category = "🔴 NOT RECOMMENDED"
        priority = 4
    
    return score, reasons, category, priority


def estimate_gdd_harvest(t_base, gdd_target, climatology, start_date):
    """
    Estimate harvest date using GDD accumulation based on historical climatology
    """
    current_gdd = 0
    days_passed = 0
    start_doy = start_date.timetuple().tm_yday
    
    # Limit simulation to 365 days to prevent infinite loops
    while current_gdd < gdd_target and days_passed < 365:
        # Get avg temp for this DOY
        # Handle leap years and wrap-around (1-366)
        doy_lookup = ((start_doy + days_passed - 1) % 365) + 1
        
        if doy_lookup in climatology.index:
            t_avg = climatology[doy_lookup]
            daily_gdd = max(0, t_avg - t_base)
            current_gdd += daily_gdd
        else:
            # Fallback if specific day missing: assume generic warm day (25C)
            daily_gdd = max(0, 25 - t_base)
            current_gdd += daily_gdd
            
        days_passed += 1
        
    harvest_date = start_date + timedelta(days=days_passed)
    return harvest_date, days_passed


def get_crop_recommendations(historical_data, current_month=None, zone_name=""):
    """
    Get ranked crop recommendations for current month
    
    Args:
        historical_data: DataFrame with historical weather data
        current_month: Month to analyze (1-12), defaults to current month
        zone_name: Name of the agricultural zone
    
    Returns:
        list: List of dicts with crop recommendations, sorted by score
    """
    if current_month is None:
        current_month = datetime.now().month

    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    # Calculate daily aggregates if needed
    if 'T_avg' not in historical_data.columns and 'T_current' in historical_data.columns:
        daily = historical_data.resample('D').agg({
            'T_current': 'mean',
            'T_max': 'max',
            'T_min': 'min',
            'Humidity': 'mean',
            'Precipitation_1h': 'sum'
        }).rename(columns={
            'T_current': 'T_avg',
            'Precipitation_1h': 'Daily_Precipitation'
        })
    else:
        daily = historical_data
    
    # Create climatology for GDD projection (Avg Temp per Day of Year)
    climatology = None
    if 'T_avg' in daily.columns:
        # Create a copy to minimize warnings
        daily_clim = daily.copy()
        daily_clim['doy'] = daily_clim.index.dayofyear
        climatology = daily_clim.groupby('doy')['T_avg'].mean()

    recommendations = []
    
    current_date = datetime.now()

    for crop_name, crop_data in SEASONAL_CROPS.items():
        score, reasons, category, priority = calculate_crop_score(
            crop_name, crop_data, current_month, daily
        )
        
        # Calculate expected harvest date using GDD if available
        if climatology is not None and 'T_base' in crop_data and 'GDD_to_Maturity' in crop_data:
            harvest_date, days_to_harvest = estimate_gdd_harvest(
                crop_data['T_base'], 
                crop_data['GDD_to_Maturity'], 
                climatology, 
                current_date
            )
            # Format: "Nov 15 (95 days)"
            expected_harvest = f"{harvest_date.strftime('%b %d')} ({days_to_harvest} days)"
        else:
            # Fallback to simple month calculation
            growing_days = crop_data['growing_season_days']
            harvest_month = (current_month + (growing_days // 30)) % 12
            expected_harvest = f"{month_names[harvest_month]} (~{growing_days} days)"
        
        # Format optimal planting months
        opt_months = [month_names[m] for m in crop_data.get('optimal_planting', [])]
        opt_text = ", ".join(opt_months) if opt_months else "See Calendar"

        recommendations.append({
            'crop': crop_name,
            'score': score,
            'category': category,
            'priority': priority,
            'reasons': reasons,
            'water_requirement': crop_data['water_requirement'],
            'soil_type': crop_data['soil_type'],
            'growing_days': crop_data['growing_season_days'], # Keep original estimate for reference
            'expected_harvest': expected_harvest,
            'season': crop_data['season'],
            'description': crop_data['description'],
            'optimal_planting': crop_data.get('optimal_planting', []),
            'optimal_planting_text': opt_text
        })
    
    # Sort by score (descending)
    recommendations.sort(key=lambda x: (-x['priority'], -x['score']))
    
    return recommendations


def get_planting_calendar(crop_name=None):
    """
    Get planting calendar for a specific crop or all crops
    
    Args:
        crop_name: Optional crop name. If None, returns calendar for all crops.
    
    Returns:
        dict: Calendar data
    """
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    if crop_name:
        if crop_name not in SEASONAL_CROPS:
            return None
        
        crop = SEASONAL_CROPS[crop_name]
        return {
            'crop': crop_name,
            'planting_months': [month_names[m-1] for m in crop['planting_months']],
            'optimal_months': [month_names[m-1] for m in crop['optimal_planting']],
            'harvest_months': [month_names[m-1] for m in crop['harvest_months']]
        }
    else:
        # Return calendar for all crops
        calendar = {}
        for crop_name, crop_data in SEASONAL_CROPS.items():
            calendar[crop_name] = {
                'planting': crop_data['planting_months'],
                'optimal': crop_data['optimal_planting'],
                'harvest': crop_data['harvest_months']
            }
        return calendar


def format_recommendation_display(recommendation):
    """
    Format a recommendation for display
    
    Args:
        recommendation: Dict with recommendation data
    
    Returns:
        str: Formatted text for display
    """
    output = f"**{recommendation['crop']}** ({recommendation['score']:.0f}% Match)\n\n"
    
    for reason in recommendation['reasons']:
        output += f"{reason}\n"
    
    output += f"\n**Details:**\n"
    output += f"- Water Needs: {recommendation['water_requirement']}\n"
    output += f"- Soil Type: {recommendation['soil_type']}\n"
    output += f"- Growing Period: {recommendation['growing_days']} days\n"
    output += f"- Expected Harvest: {recommendation['expected_harvest']}\n"
    output += f"- Season: {recommendation['season']}\n"
    
    return output
