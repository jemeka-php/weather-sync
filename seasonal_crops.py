# seasonal_crops.py
"""
Seasonal Crop Database for Abia State, Nigeria
Based on research of Nigerian agricultural seasons and local planting calendars
"""

from datetime import datetime

# Nigerian Agricultural Seasons for Abia State (Southeastern Nigeria)
SEASONS = {
    "WET_SEASON": {
        "name": "Wet Season (Main Growing Season)",
        "months": [4, 5, 6, 7, 8, 9, 10],  # April - October
        "description": "Primary growing season with abundant rainfall (>2000mm annually)",
        "characteristics": {
            "rainfall": "High (200-400mm/month)",
            "temperature": "Warm (24-30°C)",
            "humidity": "High (70-90%)",
            "farming_activities": "Main planting season for most crops"
        }
    },
    "DRY_SEASON": {
        "name": "Dry Season",
        "months": [11, 12, 1, 2, 3],  # November - March
        "description": "Dry season with Harmattan winds (Dec-Feb)",
        "characteristics": {
            "rainfall": "Low (<100mm/month)",
            "temperature": "Warm to hot (25-35°C)",
            "humidity": "Low to moderate (40-70%)",
            "farming_activities": "Dry season crops, irrigation required"
        }
    }
}

# Comprehensive Seasonal Crop Database for Abia State
SEASONAL_CROPS = {
    "Maize": {
        # Basic parameters
        "T_base": 10,
        "GDD_to_Maturity": 2500,
        "optimal_temp_range": (20, 30),
        "rainfall_annual_mm": (600, 1200),
        
        # Seasonal information
        "planting_months": [3, 4, 5, 6, 7],  # March-July (main), Aug-Nov (late season)
        "optimal_planting": [3, 4],  # March 15 - April 1 is optimal
        "harvest_months": [6, 7, 8, 9, 10, 11],
        "growing_season_days": 90,
        
        # Season classification
        "season": "Wet Season",
        "can_plant_dry_season": True,  # With irrigation
        
        # Requirements
        "water_requirement": "Moderate",
        "soil_type": "Well-drained loam",
        "irrigation_needed_dry_season": True,
        
        # Additional info
        "description": "Staple cereal crop, predominant in northern Abia districts",
        "notes": "Can be planted year-round with irrigation. Early planting (March-April) gives best yields."
    },
    
    "Rice": {
        "T_base": 12,
        "GDD_to_Maturity": 3000,
        "optimal_temp_range": (22, 32),
        "rainfall_annual_mm": (1200, 2500),
        
        "planting_months": [4, 5, 6, 7, 8],  # April-August (wet season)
        "optimal_planting": [4, 5, 6],  # April-June is optimal
        "harvest_months": [8, 9, 10, 11],
        "growing_season_days": 120,
        
        "season": "Wet Season",
        "can_plant_dry_season": False,
        
        "water_requirement": "Very High",
        "soil_type": "Clay, waterlogged suitable",
        "irrigation_needed_dry_season": True,
        
        "description": "Important cereal crop, government-supported wet season programs",
        "notes": "Lowland rice planted in April, harvested Aug-Sep. Requires consistent water supply."
    },
    
    "Cassava": {
        "T_base": 15,
        "GDD_to_Maturity": 3500,
        "optimal_temp_range": (25, 35),
        "rainfall_annual_mm": (1000, 1500),
        
        "planting_months": [3, 4, 5, 6, 7, 8],  # March-August, but April-May optimal
        "optimal_planting": [4, 5],  # Beginning of rainy season
        "harvest_months": list(range(1, 13)),  # Can harvest year-round after 12 months
        "growing_season_days": 365,  # 12 months to maturity
        
        "season": "Year-Round",
        "can_plant_dry_season": True,
        
        "water_requirement": "Low to Moderate",
        "soil_type": "Well-drained, tolerates poor soils",
        "irrigation_needed_dry_season": False,
        
        "description": "Most widely grown staple, occupies >60% of cultivated land in Abia",
        "notes": "Very drought-tolerant. Can be planted year-round in humid forest zone. Early rainy season planting ensures strong roots."
    },
    
    "Yam": {
        "T_base": 18,
        "GDD_to_Maturity": 4000,
        "optimal_temp_range": (25, 30),
        "rainfall_annual_mm": (1000, 1500),
        
        "planting_months": [12, 1, 2, 3, 4, 5, 6, 7],  # Dec-July
        "optimal_planting": [3, 4, 5],  # March-May (main season)
        "harvest_months": [10, 11, 12, 1],  # Mid-Oct to January
        "growing_season_days": 240,  # 8 months
        
        "season": "Wet Season",
        "can_plant_dry_season": True,  # Early planting Dec-Feb with mulching
        
        "water_requirement": "Moderate",
        "soil_type": "Deep, well-drained loam",
        "irrigation_needed_dry_season": False,
        
        "description": "Highest production value per area in Abia State",
        "notes": "Main planting March-May. Early dry season planting (Dec-Feb) possible with mulching. June-July good for rain-fed farmers."
    },
    
    "Cowpea": {
        "T_base": 10,
        "GDD_to_Maturity": 900,
        "optimal_temp_range": (25, 35),
        "rainfall_annual_mm": (400, 800),
        
        "planting_months": [11, 12, 1, 2, 3, 7, 8],  # Dry season and late wet season
        "optimal_planting": [12, 1, 2],  # December-February (dry season)
        "harvest_months": [2, 3, 4, 10, 11],
        "growing_season_days": 60,  # 2-3 months
        
        "season": "Dry Season",
        "can_plant_dry_season": True,
        
        "water_requirement": "Low",
        "soil_type": "Well-drained, sandy loam",
        "irrigation_needed_dry_season": False,
        
        "description": "Quick-growing legume, excellent for dry season",
        "notes": "Drought-tolerant. Perfect for dry season planting. Fixes nitrogen in soil."
    },
    
    "Groundnut (Peanut)": {
        "T_base": 12,
        "GDD_to_Maturity": 1200,
        "optimal_temp_range": (25, 33),
        "rainfall_annual_mm": (500, 1000),
        
        "planting_months": [11, 12, 1, 2, 3, 4, 5],  # Dry to early wet season
        "optimal_planting": [12, 1, 2, 3],  # Dec-March
        "harvest_months": [3, 4, 5, 6, 7, 8],
        "growing_season_days": 90,  # 3-4 months
        
        "season": "Dry Season to Early Wet",
        "can_plant_dry_season": True,
        
        "water_requirement": "Low to Moderate",
        "soil_type": "Sandy loam, well-drained",
        "irrigation_needed_dry_season": False,
        
        "description": "Drought-tolerant legume, good cash crop",
        "notes": "Excellent for dry season. Tolerates low rainfall. Improves soil fertility."
    },
    
    "Cocoyam": {
        "T_base": 15,
        "GDD_to_Maturity": 2800,
        "optimal_temp_range": (20, 28),
        "rainfall_annual_mm": (1500, 2500),
        
        "planting_months": [3, 4, 5, 6],  # Early to mid wet season
        "optimal_planting": [4, 5],  # April-May
        "harvest_months": [10, 11, 12, 1],
        "growing_season_days": 210,  # 7 months
        
        "season": "Wet Season",
        "can_plant_dry_season": False,
        
        "water_requirement": "High",
        "soil_type": "Moist, well-drained",
        "irrigation_needed_dry_season": True,
        
        "description": "Important root crop in Abia State",
        "notes": "Requires high moisture. Plant at start of rainy season."
    },
    
    "Sweet Potato": {
        "T_base": 15,
        "GDD_to_Maturity": 1800,
        "optimal_temp_range": (24, 30),
        "rainfall_annual_mm": (750, 1500),
        
        "planting_months": [3, 4, 5, 6, 7, 8],  # Wet season
        "optimal_planting": [4, 5, 6],  # April-June
        "harvest_months": [7, 8, 9, 10, 11, 12],
        "growing_season_days": 120,  # 4 months
        
        "season": "Wet Season",
        "can_plant_dry_season": True,  # With irrigation
        
        "water_requirement": "Moderate",
        "soil_type": "Well-drained, sandy loam",
        "irrigation_needed_dry_season": True,
        
        "description": "Versatile root crop",
        "notes": "Relatively drought-tolerant. Can be planted in dry season with irrigation."
    },
    
    "Melon (Egusi)": {
        "T_base": 18,
        "GDD_to_Maturity": 1000,
        "optimal_temp_range": (25, 35),
        "rainfall_annual_mm": (600, 1200),
        
        "planting_months": [3, 4, 5, 6, 7],  # Wet season
        "optimal_planting": [4, 5],  # April-May
        "harvest_months": [7, 8, 9, 10],
        "growing_season_days": 90,  # 3 months
        
        "season": "Wet Season",
        "can_plant_dry_season": False,
        
        "water_requirement": "Moderate",
        "soil_type": "Well-drained loam",
        "irrigation_needed_dry_season": True,
        
        "description": "Important vegetable crop for seeds",
        "notes": "Often intercropped with yam or cassava."
    },
    
    "Okra": {
        "T_base": 15,
        "GDD_to_Maturity": 800,
        "optimal_temp_range": (24, 35),
        "rainfall_annual_mm": (600, 1000),
        
        "planting_months": [3, 4, 5, 6, 7, 8, 9],  # Wet season
        "optimal_planting": [4, 5, 6],  # April-June
        "harvest_months": [6, 7, 8, 9, 10, 11],
        "growing_season_days": 60,  # 2 months to first harvest
        
        "season": "Wet Season",
        "can_plant_dry_season": True,  # With irrigation
        
        "water_requirement": "Moderate",
        "soil_type": "Well-drained, fertile",
        "irrigation_needed_dry_season": True,
        
        "description": "Popular vegetable crop",
        "notes": "Quick-growing. Can produce for several months."
    },
    
    "Tomato": {
        "T_base": 10,
        "GDD_to_Maturity": 1200,
        "optimal_temp_range": (20, 30),
        "rainfall_annual_mm": (500, 1000),
        
        "planting_months": [11, 12, 1, 2, 3, 8, 9],  # Dry season and late wet
        "optimal_planting": [11, 12, 1],  # Nov-Jan (dry season)
        "harvest_months": [2, 3, 4, 5, 11, 12],
        "growing_season_days": 90,  # 3 months
        
        "season": "Dry Season",
        "can_plant_dry_season": True,
        
        "water_requirement": "Moderate",
        "soil_type": "Well-drained, fertile loam",
        "irrigation_needed_dry_season": True,
        
        "description": "Significant production in northern Abia",
        "notes": "Prefers dry season to avoid fungal diseases. Requires irrigation."
    },
    
    "Pepper": {
        "T_base": 15,
        "GDD_to_Maturity": 1000,
        "optimal_temp_range": (20, 30),
        "rainfall_annual_mm": (600, 1200),
        
        "planting_months": [11, 12, 1, 2, 3, 4, 5],  # Dry to early wet
        "optimal_planting": [12, 1, 2],  # Dec-Feb
        "harvest_months": [3, 4, 5, 6, 7, 8],
        "growing_season_days": 90,  # 3 months
        
        "season": "Dry Season to Early Wet",
        "can_plant_dry_season": True,
        
        "water_requirement": "Moderate",
        "soil_type": "Well-drained, fertile",
        "irrigation_needed_dry_season": True,
        
        "description": "Important vegetable and spice crop",
        "notes": "Dry season planting reduces disease pressure."
    }
}


def get_current_season(month=None):
    """
    Determine current agricultural season for Abia State
    
    Args:
        month: Month number (1-12). If None, uses current month.
    
    Returns:
        dict: Season information
    """
    if month is None:
        month = datetime.now().month
    
    if month in SEASONS["WET_SEASON"]["months"]:
        return SEASONS["WET_SEASON"]
    else:
        return SEASONS["DRY_SEASON"]


def get_crops_for_month(month=None):
    """
    Get all crops that can be planted in a given month
    
    Args:
        month: Month number (1-12). If None, uses current month.
    
    Returns:
        list: List of crop names suitable for planting
    """
    if month is None:
        month = datetime.now().month
    
    suitable_crops = []
    for crop_name, crop_data in SEASONAL_CROPS.items():
        if month in crop_data["planting_months"]:
            suitable_crops.append(crop_name)
    
    return suitable_crops


def get_optimal_crops_for_month(month=None):
    """
    Get crops in their optimal planting window for a given month
    
    Args:
        month: Month number (1-12). If None, uses current month.
    
    Returns:
        list: List of crop names in optimal planting period
    """
    if month is None:
        month = datetime.now().month
    
    optimal_crops = []
    for crop_name, crop_data in SEASONAL_CROPS.items():
        if month in crop_data["optimal_planting"]:
            optimal_crops.append(crop_name)
    
    return optimal_crops


def is_planting_season(crop_name, month=None):
    """
    Check if it's planting season for a specific crop
    
    Args:
        crop_name: Name of the crop
        month: Month number (1-12). If None, uses current month.
    
    Returns:
        tuple: (is_plantable, is_optimal, reason)
    """
    if month is None:
        month = datetime.now().month
    
    if crop_name not in SEASONAL_CROPS:
        return False, False, "Crop not found in database"
    
    crop = SEASONAL_CROPS[crop_name]
    
    is_plantable = month in crop["planting_months"]
    is_optimal = month in crop["optimal_planting"]
    
    if is_optimal:
        reason = f"Optimal planting window for {crop_name}"
    elif is_plantable:
        reason = f"Acceptable planting period for {crop_name}"
    else:
        # Find next planting month
        next_months = [m for m in crop["planting_months"] if m > month]
        if next_months:
            next_month = min(next_months)
        else:
            next_month = min(crop["planting_months"])
        
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        reason = f"Not planting season. Next window: {month_names[next_month]}"
    
    return is_plantable, is_optimal, reason
