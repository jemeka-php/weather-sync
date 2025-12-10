# ADSS Dashboard User Guide
## How to Analyze Visualizations Across Different Timeframes

---

## Table of Contents
1. [Overview & Trends Tab](#1-overview--trends-tab)
2. [Weather Forecast Tab](#2-weather-forecast-tab)
3. [Historical Trends Tab](#3-historical-trends-tab)
4. [Risk Analysis Tab](#4-risk-analysis-tab)
5. [GDD Tracking Tab](#5-gdd-tracking-tab)
6. [Crop Planning Tab](#6-crop-planning-tab)
7. [Data Archive Tab](#7-data-archive-tab)
8. [Timeframe Selection Guide](#timeframe-selection-guide)

---

## 1. Overview & Trends Tab

### Purpose
Monitor current weather conditions and recent trends for daily farm planning.

### Key Metrics

#### Current Weather Cards
- **Temperature**: Shows current temp with comparison to average
  - **Green delta** = Warmer than average
  - **Red delta** = Cooler than average
  - **Dynamic advice** changes based on value (hot/ideal/cold)

- **Humidity**: Current moisture level in air
  - **>80%**: Warning about disease risk
  - **60-80%**: Ideal range
  - **<40%**: Warning about watering needs

- **Rainfall**: Last hour precipitation
  - Checks both current AND last 24 hours
  - Advises on irrigation needs

- **Wind Speed**: Current wind conditions
  - **>10 m/s**: Crop damage risk, avoid spraying
  - **5-10 m/s**: Not ideal for spraying
  - **<5 m/s**: Good for field work

### Statistical Summary

**Temperature Stats**
- Min/Max/Avg for selected timeframe
- Use to identify temperature extremes

**Rainfall Summary**
- **Last 30 days total**: Quick irrigation planning
  - <50mm = Increase irrigation
  - 50-100mm = Monitor closely
  - 100-200mm = Good rainfall
  - >200mm = Watch for waterlogging

### Temperature Trends Chart

**How to Read:**
- **Red line**: Daily maximum temperatures
- **Blue line**: Daily minimum temperatures  
- **Orange line**: Average temperatures

**Analysis by Timeframe:**

**Last 7 Days:**
- Spot immediate weather patterns
- Plan this week's activities
- Identify sudden temperature changes

**Last 30 Days:**
- See monthly temperature patterns
- Compare to seasonal norms
- Plan irrigation schedules

**Last 90 Days:**
- Understand seasonal transitions
- Identify long-term trends
- Plan crop rotations

**All Data:**
- See complete historical patterns
- Compare current year to past years
- Long-term climate analysis

---

## 2. Weather Forecast Tab

### Purpose
Plan farm activities for the next 48 hours and 5 days.

### Hourly Forecast (Next 48 Hours)

**What to Look For:**
- **Rain probability >60%**: Delay spraying, avoid field work
- **Temperature extremes**: Plan protective measures
- **Wind speed >5 m/s**: Postpone spraying

**Best Uses:**
- Planning pesticide application
- Scheduling irrigation
- Timing harvest activities
- Protecting sensitive crops

### Daily Forecast (Next 5 Days)

**What to Look For:**
- **Dry days**: Good for harvesting, field work
- **Rainy days**: Plan indoor tasks, check drainage
- **Temperature trends**: Prepare for heat/cold

**Planning Examples:**
- **3+ dry days ahead**: Good time to harvest
- **Rain expected**: Apply fertilizer before rain
- **Heat wave coming**: Increase irrigation

---

## 3. Historical Trends Tab

### Purpose
Understand long-term patterns and plan future seasons.

### 1. Rainfall Accumulation Over Time

**Monthly Bar Chart Analysis:**

**Last 7 Days:**
- Not applicable (too short for monthly view)

**Last 30 Days:**
- See current month's rainfall
- Compare to your irrigation plan

**Last 90 Days:**
- See 3-month rainfall pattern
- Identify wet/dry periods
- Plan seasonal crops

**All Data:**
- **Full timeline view** (Dec 2024 - present)
- Compare months across years
- Identify seasonal rainfall patterns
- **Example**: "Dec 2024 had 150mm, Jan 2025 had 80mm"

**What to Look For:**
- **Increasing bars**: Wet period, reduce irrigation
- **Decreasing bars**: Dry period, increase irrigation
- **Gaps**: Missing data months

### 2. Drought Frequency

**Monthly Line Chart Analysis:**

**Shows:** Number of drought risk days per month

**All Data View:**
- See which months typically have drought
- Plan irrigation infrastructure
- Choose drought-resistant crops for high-risk months

**What the Numbers Mean:**
- **0-5 days/month**: Low drought risk
- **5-10 days/month**: Moderate risk
- **>10 days/month**: High risk, plan irrigation

### 3. Planting Season Onset

**Scatter Plot with Trend Line:**

**Shows:** When rainy season starts each year (after March 1st)

**Analysis:**
- **Day 60-90** (March): Early onset, plant early
- **Day 90-120** (April): Normal onset
- **Day >120** (May+): Late onset, delay planting

**Trend Line:**
- **Downward**: Onset getting earlier over years
- **Upward**: Onset getting later over years
- **Flat**: Consistent timing

### 4. GDD Accumulation by Year

**Multi-Year Comparison:**

**How to Read:**
- Each colored line = Different year
- X-axis = Day of year (1-365)
- Y-axis = Cumulative GDD

**Analysis:**
- **Higher lines**: Better growing conditions that year
- **Steeper slopes**: Faster heat accumulation
- **Compare current year** to past years

---

## 4. Risk Analysis Tab

### Purpose
Early warning system for drought and waterlogging.

### Current Risk Monitor

**Gauge Chart (7-Day Rainfall):**

**Color Zones:**
- **Red (0-20mm)**: Drought risk
- **Green (20-150mm)**: Normal
- **Blue (>150mm)**: Waterlogging risk

### Risk Alerts

**Drought Alert:**
- Shows when <20mm rain in 7 days
- **Action items provided**:
  - Increase irrigation frequency
  - Check soil moisture
  - Prioritize water-sensitive crops

**Waterlogging Alert:**
- Shows when >150mm rain in 7 days
- **Action items provided**:
  - Check drainage systems
  - Monitor for crop diseases
  - Avoid field work

**Timeframe Impact:**
- **Last 7 Days**: Current risk status
- **Last 30 Days**: See risk frequency this month
- **Last 90 Days**: Seasonal risk patterns
- **All Data**: Historical risk analysis

---

## 5. GDD Tracking Tab

### Purpose
Track crop maturity and predict harvest dates.

### Key Metrics

#### 1. Estimated Planting Date
**Shows:** When crop was likely planted based on GDD accumulation

**How It's Calculated:**
- Current GDD ÷ Average daily GDD = Days since planting
- Today - Days since planting = Planting date

**Example:**
- Current GDD: 141 °C-days
- Avg daily GDD: 8.5 °C-days
- Days since planting: 141 ÷ 8.5 = 17 days
- Planting date: ~17 days ago

#### 2. Current Cumulative GDD
**Shows:** Total heat accumulated so far

**Timeframe Impact:**
- **Last 7 Days**: Recent GDD only (not useful)
- **Last 30 Days**: Monthly GDD accumulation
- **Last 90 Days**: Seasonal GDD tracking
- **All Data**: Complete crop cycle GDD

#### 3. GDD to Maturity
**Shows:** Target GDD needed for harvest

**Crop-Specific Targets:**
- Maize: 2,500 °C-days
- Rice: 3,000 °C-days
- Cowpea: 900 °C-days
- Cassava: 3,500 °C-days
- Yam: 4,000 °C-days

#### 4. Progress Percentage

**Dynamic Messages:**

**0-25%**: "Just started" - Early development
**25-50%**: "Early growth stage" - Ensure water/nutrients
**50-80%**: "Good progress" - Continue normal care
**80-100%**: "Almost ready" - Prepare for harvest
**100%**: "Crop is mature" - Ready to harvest
**105-119%**: "Slightly overdue" - Harvest within 1-2 days
**120-149%**: "OVERDUE" - Harvest ASAP, quality declining
**≥150%**: "SEVERELY OVERDUE" - Harvest immediately

**For Overdue Crops:**
- Shows estimated date when crop reached maturity
- Shows how many days overdue
- **Example**: "Should have harvested: September 24, 2024 (~76 days ago)"

#### 5. Estimated Harvest Date

**For Growing Crops (<100%):**
- Calculates days remaining based on recent GDD rate
- Shows both days and calendar date
- **Example**: "~45 days (Jan 23, 2025)"

**For Mature/Overdue Crops (≥100%):**
- Shows "Ready now or overdue"
- Displays when maturity was reached

### GDD Accumulation Chart

**Line Chart Analysis:**

**Last 6 Months View:**
- See GDD accumulation curve
- Green dashed line = Maturity target
- **Steep curve**: Fast growth (warm weather)
- **Flat curve**: Slow growth (cool weather)

**Timeframe Selection:**
- **Last 90 Days**: Current crop cycle
- **All Data**: Multiple crop cycles comparison

---

## 6. Crop Planning Tab

### Purpose
Compare current conditions to historical patterns and get crop recommendations.

### 1. Integrated Season View

**Temperature Comparison Chart:**

**Three Lines:**
- **Gray dashed**: Historical average (baseline)
- **Green solid**: Current year actuals
- **Red dotted**: 5-day forecast

**X-Axis:** Month labels (easier than day numbers)

**Analysis:**
- **Green above gray**: Warmer than normal
- **Green below gray**: Cooler than normal
- **Red line**: Future temperature trend

**Use Cases:**
- Plan planting based on temperature patterns
- Anticipate heat/cold stress
- Compare to historical norms

### 2. Cumulative Rainfall Deviation

**Metric Shows:**
- Current year rainfall vs historical average
- **Positive delta**: Wetter than normal
- **Negative delta**: Drier than normal

**Interpretation:**
- **<-20%**: Drier than normal - increase irrigation
- **-20% to +20%**: Normal range
- **>+20%**: Wetter than normal - watch drainage

### 3. Crop Suitability Assessment

**Color-Coded Table:**
- **🟢 Highly Suitable**: Best crops for your area
- **🟡 Moderately Suitable**: Can work with good management
- **🔴 Not Suitable**: Avoid these crops

**Based On:**
- Long-term temperature averages
- Rainfall patterns
- Crop requirements from CROP_PROFILES

**How to Use:**
- Focus on highly suitable crops for best yields
- Moderately suitable crops need extra care (irrigation, fertilizer)

### 4. Planting Window Advisory

**Shows:** Recommended planting period based on historical rainfall

**Typical Window:** March 15 - April 30

**Why This Period:**
- Rain usually starts
- Soil warm enough for germination
- Sufficient growing season ahead

---

## 7. Data Archive Tab

### Purpose
View and download raw weather data.

### Recent Records Table

**Columns:**
- Timestamp
- Zone
- Temperature (Current, Min, Max)
- Humidity
- Precipitation
- Wind Speed
- Pressure

**Timeframe Impact:**
- **Last 7 Days**: ~168 hourly records
- **Last 30 Days**: ~720 hourly records
- **Last 90 Days**: ~2,160 hourly records
- **All Data**: Complete dataset

**Use Cases:**
- Export data for external analysis
- Verify specific weather events
- Create custom reports
- Quality check data

---

## Timeframe Selection Guide

### When to Use Each Timeframe

#### Last 7 Days
**Best For:**
- Daily farm operations
- Immediate decision making
- Spotting sudden changes
- Short-term planning

**Limitations:**
- No long-term trends
- Can't see seasonal patterns
- Limited historical context

#### Last 30 Days
**Best For:**
- Monthly planning
- Irrigation scheduling
- Identifying recent patterns
- Comparing to monthly norms

**Good Balance:**
- Enough data for trends
- Recent enough to be relevant
- Manageable data volume

#### Last 90 Days
**Best For:**
- Seasonal analysis
- Crop cycle tracking
- GDD accumulation
- Quarterly planning

**Advantages:**
- Full seasonal view
- Multiple weather patterns
- Crop growth tracking

#### All Data
**Best For:**
- Year-over-year comparisons
- Long-term trend analysis
- Climate pattern identification
- Historical research

**Considerations:**
- Large dataset
- May include incomplete years
- Best for strategic planning

---

## Best Practices

### 1. Daily Routine
- Check **Overview & Trends** (Last 7 Days)
- Review **Weather Forecast** (Next 48 hours)
- Monitor **Risk Analysis** (Current status)

### 2. Weekly Planning
- Review **Overview & Trends** (Last 30 Days)
- Check **GDD Tracking** (Last 90 Days)
- Plan activities based on **Weather Forecast**

### 3. Seasonal Planning
- Analyze **Historical Trends** (All Data)
- Review **Crop Planning** recommendations
- Compare **GDD Tracking** across timeframes

### 4. Decision Making

**Irrigation:**
- Check 30-day rainfall summary
- Review 7-day forecast
- Monitor risk analysis

**Planting:**
- Check planting window advisory
- Review historical onset dates
- Verify current soil temperature (via GDD)

**Harvesting:**
- Monitor GDD progress
- Check 5-day forecast
- Ensure dry weather ahead

**Spraying:**
- Check hourly forecast
- Verify wind speed <5 m/s
- Ensure no rain for 24 hours

---

## Troubleshooting

### "Insufficient data" Messages
- **Cause**: Selected timeframe has no data
- **Solution**: Try "All Data" or different timeframe

### Charts Not Showing
- **Cause**: Data filtering removed all records
- **Solution**: Select longer timeframe or different zone

### GDD Shows 0%
- **Cause**: Not enough data or wrong crop selected
- **Solution**: Select "All Data" timeframe

### Forecast Not Available
- **Cause**: API connection issue
- **Solution**: Check internet connection, try refreshing

---

## Glossary

**GDD (Growing Degree Days)**: Heat units accumulated for crop growth  
**T_base**: Minimum temperature for crop growth  
**Maturity**: When crop reaches target GDD  
**Onset**: Start of rainy season  
**YTD**: Year To Date  
**Cumulative**: Running total over time  
**Deviation**: Difference from average  
**Drought Risk**: <20mm rain in 7 days  
**Waterlogging Risk**: >150mm rain in 7 days

---

## Quick Reference Card

| Task | Tab | Timeframe | Key Metric |
|------|-----|-----------|------------|
| Plan today's work | Overview | Last 7 Days | Current metrics |
| Schedule irrigation | Overview | Last 30 Days | Rainfall summary |
| Check harvest readiness | GDD Tracking | Last 90 Days | Progress % |
| Plan next season | Historical Trends | All Data | Annual patterns |
| Spray pesticides | Forecast | Next 48 Hours | Rain probability |
| Choose crops | Crop Planning | All Data | Suitability table |
| Monitor risks | Risk Analysis | Last 7 Days | Risk gauge |

---

*For technical support or questions, refer to the project documentation or contact the development team.*
