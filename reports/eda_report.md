# Exploratory Data Analysis (EDA) Report
## AI-Based Medicine Demand Forecasting & Inventory Optimization

---

### 1. Overall Demand Distribution & Statistics
- **Total Historical Records**: 19,728 across 18 medicines
- **Mean Daily Demand**: 78.21 units
- **Standard Deviation**: 41.45 units
- **Median Daily Demand**: 71.0 units
- **Interquartile Range (IQR)**: 45.0 units
- **Skewness**: 1.65 (moderate positive right-skew typical of count/surge processes)
- **Minimum Daily Sold**: 0 units
- **Peak Surge Observed**: 453 units

---

### 2. Top 10 Medicines by Cumulative Demand
| Rank | Medicine | Category | Total Demand | Avg Daily Demand | Std Dev | CV (Volatility) | Outlier Days |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **Paracetamol** | Analgesic & Antipyretic | 195,556 | 178.4 | 50.2 | 0.281 | 24 |
| 2 | **Vitamin C** | Vitamins & Immunity | 128,510 | 117.3 | 33.6 | 0.286 | 32 |
| 3 | **Metformin** | Antidiabetic | 115,612 | 105.5 | 20.3 | 0.192 | 15 |
| 4 | **Omeprazole** | Gastrointestinal | 103,508 | 94.4 | 19.5 | 0.206 | 24 |
| 5 | **Ibuprofen** | NSAID & Pain Relief | 97,924 | 89.3 | 19.8 | 0.221 | 27 |
| 6 | **Pantoprazole** | Gastrointestinal | 95,020 | 86.7 | 18.5 | 0.214 | 34 |
| 7 | **Cetirizine** | Antihistamine & Allergy | 93,764 | 85.6 | 32.4 | 0.378 | 26 |
| 8 | **Cough Syrup** | Respiratory | 87,404 | 79.7 | 33.2 | 0.416 | 20 |
| 9 | **Atorvastatin** | Cardiovascular | 82,606 | 75.4 | 15.9 | 0.211 | 22 |
| 10 | **Amlodipine** | Cardiovascular | 76,562 | 69.9 | 14.3 | 0.205 | 16 |

---

### 3. Key Demand Patterns for Feature Engineering

#### A. Temporal Patterns
1. **Day-of-Week Effect**:
   - Weekends show higher average demand for acute/OTC products (+12% to +18%), while chronic prescription refills drop slightly on Sundays.
   - Recommended features: `day_of_week`, `is_weekend`, `is_saturday`, `is_sunday`.

2. **Monthly & Seasonal Dynamics**:
   - Peak general medicine consumption occurs in **Winter** (flu/fever season) and **Monsoon** (waterborne/seasonal infections).
   - Antihistamines (**Cetirizine**, **Montelukast**) peak in **Spring** (pollen) and **Monsoon**.
   - Rehydration electrolytes (**ORS**) display severe positive correlation with summer temperatures (>32°C).
   - Recommended features: `month_sin`, `month_cos`, `season_encoded`, `quarter`.

3. **Holiday Patterns**:
   - Regular Days Mean Demand: 78.26 units
   - Holiday Days Mean Demand: 76.09 units
   - Recommended features: `is_holiday`, `days_to_next_holiday`, `days_since_last_holiday`.

#### B. Environmental & Weather Drivers
- **Temperature**: Strong driver for ORS (positive) and Antibiotics/Analgesics (inverse with cold waves).
- **Rainfall**: Strong catalyst for respiratory and gastrointestinal infection surge periods.
- Recommended features: `temp_rolling_7d_mean`, `rainfall_rolling_3d_sum`, `extreme_heat_indicator`.

#### C. Inventory Dynamics
- Reorder threshold replenishment behavior demonstrates cyclical sawtooth stock behavior. Stockouts are rare, and `Stock_Level` safely absorbs daily demand variability.
- Recommended features: `stock_level_lag1`, `days_of_supply_remaining` (`Stock_Level / rolling_mean_demand`).

---

### 4. Generated EDA Visualizations
- [01_medicine_demand_bar.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/01_medicine_demand_bar.png)
- [02_daily_demand_timeline.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/02_daily_demand_timeline.png)
- [03_monthly_demand_trend.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/03_monthly_demand_trend.png)
- [04_day_of_week_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/04_day_of_week_demand.png)
- [05_seasonal_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/05_seasonal_demand.png)
- [06_correlation_heatmap.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/06_correlation_heatmap.png)
- [07_demand_distribution.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/07_demand_distribution.png)
- [08_stock_vs_demand.png](file:///c:/Users/manoj/projects/medicine%20demand/reports/figures/08_stock_vs_demand.png)
- Interactive Dashboard: [interactive_eda.html](file:///c:/Users/manoj/projects/medicine%20demand/reports/interactive_eda.html)
