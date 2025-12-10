# Abia State Agricultural Decision Support System (ADSS)

## 📌 Project Overview
The **Abia State Agricultural Decision Support System (ADSS)** is a specialized software solution designed to empower farmers and agricultural stakeholders in Abia State with real-time, data-driven insights. By integrating automated weather monitoring, historical climate analysis, and agronomic modeling, the system aids in critical farm management decisions to enhance crop productivity and resilience.

## 🎯 Project Goals
1.  **Automate Data Collection**: Continuously retrieve and archive hyper-local weather data for key agricultural zones (Aba, Umuahia, Bende).
2.  **Mitigate Climate Risk**: Provide real-time alerts for drought and waterlogging events based on localized thresholds.
3.  **Optimize Planting Schedules**: Utilize historical rainfall onset data and Growing Degree Days (GDD) to recommend optimal planting and harvest windows.
4.  **Enhance Crop Planning**: Assess crop suitability dynamically by comparing current seasonal trajectories against historical baselines and future forecasts.

---

## 🚀 Key Features & Detailed Feature Breakdown
The application is structured into **7 interactive modules** (tabs), each providing specific analytical capabilities:

### 📊 1. Overview & Trends
**Purpose**: Instant snapshot of current environmental conditions.
*   **Real-time Metrics**: Displays current Temperature, Humidity, Wind Speed, and recent Rainfall.
*   **Statistical Summary**: Aggregates rolling averages (30-day/90-day rainfall) to provide context.
*   **Temperature Trends**: Interactive line charts showing daily Max/Min/Current temperature variations.

### 🔮 2. Weather Forecast
**Purpose**: Short-term planning aid for immediate farm operations (spraying, fertilizer application).
*   **48-Hour Hourly Forecast**: Detailed timeline of Temperature and Precipitation Probability (%) to time field activities.
*   **5-Day Daily Outlook**: High-level summary of upcoming weather patterns for weekly planning.

### 📜 3. Historical Trends
**Purpose**: Long-term climate analysis for strategic planning.
*   **Annual Rainfall Comparison**: Bar charts tracking total precipitation year-over-year (2020-Present).
*   **Drought Frequency**: Analysis of historical drought risk days per year.
*   **Planting Onset Estimation**: Algorithms that identify the start of the planting season based on rainfall consistency (>20mm in 3 days after March 1st).

### 💧 4. Risk Analysis
**Purpose**: Early warning system for extreme weather events.
*   **Rolling 7-Day Rainfall**: Calculates cumulative rainfall over a sliding 7-day window.
*   **Automated Alerts**: 
    *   🚨 **Drought Risk**: < 5.0 mm rainwater in 7 days.
    *   ⚠️ **Waterlogging Risk**: > 150.0 mm rainwater in 7 days.
*   **Trend Visualization**: Color-coded charts highlighting periods of risk.

### 🌱 5. GDD Tracking (Growing Degree Days)
**Purpose**: Phenological tracking to estimate crop maturity.
*   **Crop-Specific Logic**: Calculates GDD based on specific *T_base* derived from crop profiles (e.g., Maize, Cassava, Yam).
*   **Maturity Progress**: Metric showing % progress significantly towards the target GDD (Heat Units) required for harvest.
*   **Accumulation Chart**: Visualizes heat unit accumulation over the last 6 months.

### 🗓️ 6. Crop Planning
**Purpose**: Strategic decision support combining past, present, and future data.
*   **Integrated Season View**: A powerful chart overlaying the **Current Year's** temperature trajectory against the **Historical Average** (Baseline) and the **5-Day Forecast**.
*   **Deviation Analysis**: Quantifies how much the current season deviates (Wetter/Drier, Hotter/Cooler) from the historical norm.
*   **Suitability Assessment**: Algorithms that score the zone's long-term climate against the specific agronomic requirements of crops (Rainfall range, Temp optimal range).

### 📁 7. Data Archive
**Purpose**: Transparency and data portability.
*   **Raw Data Viewer**: Tabular view of the collected dataset.
*   **Export Capability**: One-click download of the complete dataset (`.csv`) for external analysis.

---

## 👥 Uses & Applications
*   **Farm Managers**: Determine the detailed "When" for planting, spraying, and harvesting based on micro-climate data.
*   **Policy Makers & Extension Officers**: Monitor regional drought risks and provide timely advisories to rural communities.
*   **Researchers**: Analyze long-term climate shifts in Abia State without needing to maintain physical weather stations.
*   **Automation**: The GitHub Actions workflow serves as a zero-maintenance "Virtual Weather Station", collecting data every 6 hours automatically.

## 📦 Contents (Modules)
The project codebase consists of the following key components:
*   `dashboard.py`: The main visualization application built with Streamlit.
*   `data_collector.py`: The robust backend script for fetching API data and syncing to Supabase.
*   `config.py`: Centralized configuration for Crop Profiles, API Keys, and risk thresholds.
*   `.github/workflows/weather_sync.yml`: The automation engine that schedules data collection.

---

## 📉 Key Metrics & Agronomic Computations (Appendix)

Understanding the data is crucial for using the ADSS effectively. Below are the core metrics tracked by the system, their mathematical basis, and their practical impact on farming.

### 1. Growing Degree Days (GDD)
*   **Formula**: $$GDD = \max(0, T_{avg} - T_{base})$$
    *   Where $$T_{avg} = \frac{(T_{max} + T_{min})}{2}$$
    *   $$T_{base}$$ is the crop-specific base temperature (e.g., 10°C for Maize).
*   **Meaning**: Plants count "heat units," not calendar days. GDD measures the daily accumulation of useful heat for growth.
*   **Impact on Farmers**:
    *   **Predicts Harvest**: Helps farmers know exactly when crops will reach maturity regardless of weather fluctuations.
    *   **Pest Planning**: Many pests emerge only after specific GDD thresholds.

### 2. Relative Humidity (RH)
*   **Definition**: The amount of water vapor in the air relative to what the air can hold at that temperature.
*   **Impact on Farmers**:
    *   **High RH (>80%)**: drastically increases the risk of **Fungal Diseases** (e.g., Late Blight in potatoes/tomatoes).
    *   **Low RH (<40%)**: leads to rapid water loss (transpiration), causing crop stress even if soil is moist.

### 3. Cumulative Rainfall (Rolling 7-Day Sum)
*   **Formula**: $$\sum_{i=0}^{6} Rainfall_{day-i}$$
*   **Meaning**: The total millimeters of rain received over the last week.
*   **Impact on Farmers**:
    *   **Drought Risk (<5mm)**: Signals a need for supplemental irrigation or mulching to preserve soil moisture.
    *   **Waterlogging Risk (>150mm)**: Warns of root suffocation risk; farmers should clear drainage channels immediately.

### 4. Temperature Extremes ($$T_{max}$$ and $$T_{min}$$)
*   **Measurement**: The highest and lowest air temperatures recorded in a 24-hour period.
*   **Impact on Farmers**:
    *   **Heat Stress ($$T_{max} > 35^\circ C$$)**: Causes flower abortion in crops like Maize and Tomato, reducing yields.
    *   **Chilling Injury ($$T_{min} < 10^\circ C$$)**: Stunts growth in tropical crops like Yam and Cassava.

### 5. Wind Speed & Direction
*   **Measurement**: Speed in meters per second (m/s) and cardinal direction.
*   **Impact on Farmers**:
    *   **Spraying Operations**: Herbicides/Pesticides should NOT be sprayed if wind speed > 5 m/s to prevent "drift" onto neighboring fields or homes.
    *   **Physical Damage**: Winds > 10 m/s can cause lodging (stalks breaking) in mature Maize/Rice fields.
