"""
Realistic Synthetic Dataset Generator for Medicine Demand Forecasting.

Generates 3 years of daily historical data across 18 diverse medicines,
incorporating seasonal trends, weather sensitivity, day-of-week effects,
holidays, demand spikes, and dynamic inventory stock levels.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


# Set fixed seeds for full reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# 1. Define Medicines and Categorization
MEDICINE_PROFILES = {
    "Paracetamol": {
        "category": "Analgesic & Antipyretic",
        "base_demand": 130,
        "unit_price": 2.50,
        "temp_sensitivity": "cold",      # Higher in cold weather (fever/flu)
        "rain_sensitivity": 0.2,
        "season_boost": {"Winter": 1.35, "Monsoon": 1.20, "Spring": 1.00, "Summer": 0.90, "Autumn": 1.05},
        "weekend_boost": 1.15,
        "is_chronic": False,
    },
    "Ibuprofen": {
        "category": "NSAID & Pain Relief",
        "base_demand": 75,
        "unit_price": 4.20,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.1,
        "season_boost": {"Winter": 1.15, "Monsoon": 1.05, "Spring": 1.00, "Summer": 0.95, "Autumn": 1.00},
        "weekend_boost": 1.10,
        "is_chronic": False,
    },
    "Amoxicillin": {
        "category": "Antibiotic",
        "base_demand": 45,
        "unit_price": 8.50,
        "temp_sensitivity": "cold",
        "rain_sensitivity": 0.35,
        "season_boost": {"Winter": 1.40, "Monsoon": 1.30, "Spring": 0.95, "Summer": 0.80, "Autumn": 1.10},
        "weekend_boost": 0.95,
        "is_chronic": False,
    },
    "Azithromycin": {
        "category": "Antibiotic",
        "base_demand": 32,
        "unit_price": 15.00,
        "temp_sensitivity": "cold",
        "rain_sensitivity": 0.30,
        "season_boost": {"Winter": 1.45, "Monsoon": 1.25, "Spring": 0.90, "Summer": 0.75, "Autumn": 1.05},
        "weekend_boost": 0.90,
        "is_chronic": False,
    },
    "Cetirizine": {
        "category": "Antihistamine & Allergy",
        "base_demand": 65,
        "unit_price": 3.00,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.40,
        "season_boost": {"Spring": 1.50, "Monsoon": 1.35, "Autumn": 1.10, "Winter": 0.85, "Summer": 0.80},
        "weekend_boost": 1.10,
        "is_chronic": False,
    },
    "Omeprazole": {
        "category": "Gastrointestinal",
        "base_demand": 80,
        "unit_price": 5.50,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.05,
        "season_boost": {"Winter": 1.05, "Monsoon": 1.05, "Spring": 1.00, "Summer": 1.00, "Autumn": 1.00},
        "weekend_boost": 1.12,
        "is_chronic": False,
    },
    "Pantoprazole": {
        "category": "Gastrointestinal",
        "base_demand": 75,
        "unit_price": 6.00,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.05,
        "season_boost": {"Winter": 1.02, "Monsoon": 1.04, "Spring": 1.00, "Summer": 1.00, "Autumn": 1.00},
        "weekend_boost": 1.10,
        "is_chronic": False,
    },
    "Metformin": {
        "category": "Antidiabetic",
        "base_demand": 100,
        "unit_price": 4.00,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.0,
        "season_boost": {"Winter": 1.00, "Monsoon": 1.00, "Spring": 1.00, "Summer": 1.00, "Autumn": 1.00},
        "weekend_boost": 0.90,
        "is_chronic": True,
    },
    "Amlodipine": {
        "category": "Cardiovascular",
        "base_demand": 65,
        "unit_price": 3.80,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.0,
        "season_boost": {"Winter": 1.02, "Monsoon": 1.00, "Spring": 1.00, "Summer": 0.98, "Autumn": 1.00},
        "weekend_boost": 0.92,
        "is_chronic": True,
    },
    "Atorvastatin": {
        "category": "Cardiovascular",
        "base_demand": 70,
        "unit_price": 7.20,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.0,
        "season_boost": {"Winter": 1.01, "Monsoon": 1.00, "Spring": 1.00, "Summer": 1.00, "Autumn": 1.00},
        "weekend_boost": 0.91,
        "is_chronic": True,
    },
    "ORS": {
        "category": "Rehydration & Electrolytes",
        "base_demand": 45,
        "unit_price": 2.00,
        "temp_sensitivity": "hot",       # Strongly surges during hot summer
        "rain_sensitivity": 0.50,      # Waterborne illness in monsoon
        "season_boost": {"Summer": 2.20, "Monsoon": 1.60, "Spring": 1.10, "Autumn": 0.70, "Winter": 0.45},
        "weekend_boost": 1.20,
        "is_chronic": False,
    },
    "Insulin": {
        "category": "Antidiabetic",
        "base_demand": 28,
        "unit_price": 32.00,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.0,
        "season_boost": {"Winter": 1.00, "Monsoon": 1.00, "Spring": 1.00, "Summer": 1.00, "Autumn": 1.00},
        "weekend_boost": 0.88,
        "is_chronic": True,
    },
    "Vitamin C": {
        "category": "Vitamins & Immunity",
        "base_demand": 85,
        "unit_price": 3.50,
        "temp_sensitivity": "cold",
        "rain_sensitivity": 0.25,
        "season_boost": {"Winter": 1.30, "Monsoon": 1.25, "Spring": 1.00, "Summer": 0.90, "Autumn": 1.05},
        "weekend_boost": 1.15,
        "is_chronic": False,
    },
    "Aspirin": {
        "category": "Analgesic & Antiplatelet",
        "base_demand": 55,
        "unit_price": 2.80,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.05,
        "season_boost": {"Winter": 1.05, "Monsoon": 1.00, "Spring": 1.00, "Summer": 0.98, "Autumn": 1.00},
        "weekend_boost": 0.98,
        "is_chronic": True,
    },
    "Diclofenac": {
        "category": "NSAID & Pain Relief",
        "base_demand": 50,
        "unit_price": 5.00,
        "temp_sensitivity": "cold",      # Joint pain increases in cold/damp weather
        "rain_sensitivity": 0.20,
        "season_boost": {"Winter": 1.25, "Monsoon": 1.15, "Spring": 0.95, "Summer": 0.90, "Autumn": 1.00},
        "weekend_boost": 1.08,
        "is_chronic": False,
    },
    "Cough Syrup": {
        "category": "Respiratory",
        "base_demand": 55,
        "unit_price": 9.00,
        "temp_sensitivity": "cold",
        "rain_sensitivity": 0.45,
        "season_boost": {"Winter": 1.55, "Monsoon": 1.35, "Spring": 0.90, "Summer": 0.65, "Autumn": 1.10},
        "weekend_boost": 1.18,
        "is_chronic": False,
    },
    "Montelukast": {
        "category": "Respiratory & Allergy",
        "base_demand": 38,
        "unit_price": 11.50,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.35,
        "season_boost": {"Spring": 1.45, "Monsoon": 1.30, "Winter": 1.15, "Autumn": 1.00, "Summer": 0.85},
        "weekend_boost": 0.94,
        "is_chronic": True,
    },
    "Losartan": {
        "category": "Cardiovascular",
        "base_demand": 52,
        "unit_price": 6.50,
        "temp_sensitivity": "neutral",
        "rain_sensitivity": 0.0,
        "season_boost": {"Winter": 1.01, "Monsoon": 1.00, "Spring": 1.00, "Summer": 0.99, "Autumn": 1.00},
        "weekend_boost": 0.90,
        "is_chronic": True,
    },
}


def get_season(month: int) -> str:
    """Determine seasonal classification from calendar month."""
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4]:
        return "Spring"
    elif month in [5, 6]:
        return "Summer"
    elif month in [7, 8, 9]:
        return "Monsoon"
    else:
        return "Autumn"


def generate_holiday_calendar(start_date: datetime, end_date: datetime) -> set:
    """Generate fixed and key national/seasonal holidays."""
    holidays = set()
    for year in range(start_date.year, end_date.year + 1):
        # Fixed holidays
        fixed_dates = [
            (1, 1),    # New Year
            (1, 26),   # Republic Day / National Day
            (5, 1),    # Labor Day
            (8, 15),   # Independence Day
            (10, 2),   # National Memorial Day
            (12, 25),  # Christmas
        ]
        for m, d in fixed_dates:
            try:
                holidays.add(datetime(year, m, d).strftime("%Y-%m-%d"))
            except ValueError:
                pass

        # Seasonal festival windows (approximate dates)
        festivals = [
            (3, 15),   # Spring Festival
            (10, 24),  # Autumn Festival / Diwali
            (11, 12),  # Mid-Autumn celebration
        ]
        for m, d in festivals:
            try:
                holidays.add(datetime(year, m, d).strftime("%Y-%m-%d"))
            except ValueError:
                pass

    return holidays


def simulate_weather(date: datetime) -> tuple:
    """
    Generate realistic temperature and rainfall based on day of year.
    Temperature has smooth seasonal oscillation + daily jitter.
    Rainfall has monsoon concentration with zero-inflated Gamma distribution.
    """
    day_of_year = date.timetuple().tm_yday
    month = date.month

    # Seasonal temperature curve: peak ~35C in May/June (day ~145), low ~16C in Jan (day ~15)
    radians = 2 * np.pi * (day_of_year - 145) / 365.0
    mean_temp = 26.0 + 9.0 * np.cos(radians)
    daily_temp = mean_temp + np.random.normal(0, 2.0)
    temperature = round(float(np.clip(daily_temp, 8.0, 44.0)), 1)

    # Rainfall pattern: heavy during Monsoon (months 7, 8, 9), sporadic in Summer/Spring
    if month in [7, 8, 9]:
        # 60% probability of rain during monsoon
        if np.random.rand() < 0.60:
            rain = np.random.gamma(shape=2.5, scale=12.0)
        else:
            rain = 0.0
    elif month in [5, 6]:
        # Pre-monsoon thundershowers
        if np.random.rand() < 0.20:
            rain = np.random.gamma(shape=1.5, scale=8.0)
        else:
            rain = 0.0
    elif month in [10, 11]:
        # Post-monsoon retreat
        if np.random.rand() < 0.15:
            rain = np.random.gamma(shape=1.2, scale=5.0)
        else:
            rain = 0.0
    else:
        # Dry winter / spring
        if np.random.rand() < 0.05:
            rain = np.random.exponential(scale=3.0)
        else:
            rain = 0.0

    rainfall = round(float(np.clip(rain, 0.0, 140.0)), 1)
    return temperature, rainfall


def generate_medicine_dataset(
    start_date_str: str = "2022-01-01",
    end_date_str: str = "2024-12-31",
    output_path: str = "dataset/medicine_demand.csv",
) -> pd.DataFrame:
    """Generate 3 years of synthetic medicine demand records."""
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    total_days = (end_date - start_date).days + 1

    holidays = generate_holiday_calendar(start_date, end_date)

    records = []

    # Track simulated inventory state per medicine across time
    inventory_state = {}
    for med, prof in MEDICINE_PROFILES.items():
        base = prof["base_demand"]
        target_capacity = base * 12      # ~12 days of stock capacity
        reorder_point = base * 4         # Reorder when below 4 days of stock
        reorder_qty = base * 8           # Reorder quantity
        inventory_state[med] = {
            "current_stock": target_capacity,
            "target_capacity": target_capacity,
            "reorder_point": reorder_point,
            "reorder_qty": reorder_qty,
            "pending_delivery_days": 0,
        }

    # Generate daily records chronologically
    current_date = start_date
    day_idx = 0

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        day_of_week = current_date.strftime("%A")
        month_name = current_date.strftime("%B")
        month_int = current_date.month
        season = get_season(month_int)
        is_weekend = int(current_date.weekday() >= 5)
        is_holiday = int(date_str in holidays)

        # Weather for the day
        temperature, rainfall = simulate_weather(current_date)

        # Global macroeconomic secular trend (+4.5% demand growth per year)
        year_offset = (current_date - start_date).days / 365.25
        secular_trend = 1.0 + (0.045 * year_offset)

        # Occasional regional health events (e.g. viral wave, heatwave)
        # Small chance of a community-level surge
        community_surge = 1.0
        if season == "Monsoon" and rainfall > 40.0:
            community_surge = 1.25
        elif season == "Summer" and temperature > 38.0:
            community_surge = 1.20
        elif season == "Winter" and temperature < 14.0:
            community_surge = 1.20

        for med, prof in MEDICINE_PROFILES.items():
            base_demand = prof["base_demand"]
            category = prof["category"]
            unit_price = prof["unit_price"]

            # 1. Seasonality modifier
            season_mult = prof["season_boost"].get(season, 1.0)

            # 2. Temperature effect
            temp_mult = 1.0
            if prof["temp_sensitivity"] == "cold":
                # Drops in hot temp, rises in cold temp
                temp_mult = 1.0 + 0.02 * max(0, 24.0 - temperature)
            elif prof["temp_sensitivity"] == "hot":
                # ORS / hydration surges above 30C
                temp_mult = 1.0 + 0.04 * max(0, temperature - 28.0)

            # 3. Rainfall effect
            rain_mult = 1.0 + (prof["rain_sensitivity"] * (rainfall / 50.0))

            # 4. Day of week effect
            if is_weekend:
                dow_mult = prof["weekend_boost"]
            else:
                dow_mult = 1.0

            # 5. Holiday effect
            if is_holiday:
                if prof["is_chronic"]:
                    # Chronic refills dip on holidays (clinics closed)
                    holiday_mult = 0.75
                else:
                    # Acute/first aid sees small emergency bump
                    holiday_mult = 1.10
            else:
                holiday_mult = 1.0

            # 6. Random demand noise and occasional stochastic spikes
            # Log-normal noise around 1.0
            noise = np.random.lognormal(mean=0.0, sigma=0.12)

            # Sporadic rare demand spike (1.5% probability, e.g. bulk hospital purchase)
            spike_mult = 1.0
            if np.random.rand() < 0.015:
                spike_mult = np.random.uniform(1.4, 2.0)

            # Composite expected demand
            expected_demand = (
                base_demand
                * secular_trend
                * season_mult
                * temp_mult
                * rain_mult
                * dow_mult
                * holiday_mult
                * community_surge
                * spike_mult
                * noise
            )

            # Sold quantity is Poisson distributed around expected demand
            quantity_sold = int(np.random.poisson(lam=max(1.0, expected_demand)))

            # Inventory simulation
            inv = inventory_state[med]

            # Handle incoming stock delivery
            if inv["pending_delivery_days"] > 0:
                inv["pending_delivery_days"] -= 1
                if inv["pending_delivery_days"] == 0:
                    inv["current_stock"] += inv["reorder_qty"]

            # Cap sold by stock on hand if stockout occurs (rare in realistic stock policy)
            actual_sold = min(quantity_sold, inv["current_stock"])
            inv["current_stock"] = max(0, inv["current_stock"] - actual_sold)

            # Record stock level at start/end of day
            recorded_stock = inv["current_stock"]

            # Trigger reorder if below threshold and not already pending
            if (inv["current_stock"] <= inv["reorder_point"]) and (inv["pending_delivery_days"] == 0):
                # Lead time: 1 to 3 days
                inv["pending_delivery_days"] = np.random.randint(1, 4)

            records.append({
                "Date": date_str,
                "Medicine": med,
                "Medicine_Category": category,
                "Quantity_Sold": actual_sold,
                "Stock_Level": recorded_stock,
                "Unit_Price": unit_price,
                "Day_of_Week": day_of_week,
                "Month": month_name,
                "Season": season,
                "Is_Weekend": is_weekend,
                "Is_Holiday": is_holiday,
                "Temperature": temperature,
                "Rainfall": rainfall,
            })

        current_date += timedelta(days=1)
        day_idx += 1

    df = pd.DataFrame(records)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def print_dataset_summary(df: pd.DataFrame, output_path: str):
    """Display verification summary and basic statistics."""
    print("=" * 65)
    print("MEDICINE DEMAND DATASET GENERATION SUMMARY")
    print("=" * 65)
    print(f"File Path:          {output_path}")
    print(f"Number of Rows:     {len(df):,}")
    print(f"Number of Columns:  {len(df.columns)}")
    print(f"Number of Medicines:{df['Medicine'].nunique()}")
    print(f"Categories Count:   {df['Medicine_Category'].nunique()}")
    print(f"Date Range:         {df['Date'].min()} to {df['Date'].max()} ({(pd.to_datetime(df['Date'].max()) - pd.to_datetime(df['Date'].min())).days + 1} days)")
    print("-" * 65)
    print("MISSING VALUES:")
    print(df.isnull().sum())
    print("-" * 65)
    print("MEDICINES LIST:")
    for med, cat in df[["Medicine", "Medicine_Category"]].drop_duplicates().values:
        mean_qty = df[df["Medicine"] == med]["Quantity_Sold"].mean()
        print(f" - {med:<15} ({cat:<26}) Avg Daily Sold: {mean_qty:.1f}")
    print("-" * 65)
    print("BASIC NUMERICAL STATISTICS:")
    num_cols = ["Quantity_Sold", "Stock_Level", "Unit_Price", "Temperature", "Rainfall"]
    print(df[num_cols].describe().round(2))
    print("=" * 65)


if __name__ == "__main__":
    out_file = os.path.join("dataset", "medicine_demand.csv")
    df_generated = generate_medicine_dataset(
        start_date_str="2022-01-01",
        end_date_str="2024-12-31",
        output_path=out_file,
    )
    print_dataset_summary(df_generated, out_file)
