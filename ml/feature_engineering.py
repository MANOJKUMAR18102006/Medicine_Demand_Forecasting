"""
Feature Engineering Module for Medicine Demand Forecasting.

Extracts calendar indicators, cyclical trigonometric signals, historical autoregressive lags,
leakage-free rolling demand aggregations, weather moving averages, inventory ratios, and categorical
encodings. Ensures strict temporal causality (no data leakage).
"""

import os
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd


def load_cleaned_dataset(file_path: str = "dataset/cleaned_medicine_demand.csv") -> pd.DataFrame:
    """Load cleaned medicine consumption dataset and parse dates."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cleaned dataset not found at: {file_path}")
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df.sort_values(by=["Medicine", "Date"]).reset_index(drop=True)


def create_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract calendar date features and smooth cyclical trigonometric transforms.
    
    Includes:
    - Year, Month, Day, DayOfWeek (0=Mon..6=Sun), WeekOfYear, Quarter, IsWeekend.
    - Sine/Cosine transforms for Month and DayOfWeek to model circular continuity.
    """
    df_feat = df.copy()
    
    df_feat["Year"] = df_feat["Date"].dt.year
    df_feat["Month"] = df_feat["Date"].dt.month
    df_feat["Day"] = df_feat["Date"].dt.day
    df_feat["DayOfWeek"] = df_feat["Date"].dt.dayofweek
    df_feat["WeekOfYear"] = df_feat["Date"].dt.isocalendar().week.astype(int)
    df_feat["Quarter"] = df_feat["Date"].dt.quarter
    df_feat["IsWeekend"] = (df_feat["DayOfWeek"] >= 5).astype(int)

    # Trigonometric cyclical features
    df_feat["Month_Sin"] = np.sin(2 * np.pi * df_feat["Month"] / 12.0).round(4)
    df_feat["Month_Cos"] = np.cos(2 * np.pi * df_feat["Month"] / 12.0).round(4)
    df_feat["DayOfWeek_Sin"] = np.sin(2 * np.pi * df_feat["DayOfWeek"] / 7.0).round(4)
    df_feat["DayOfWeek_Cos"] = np.cos(2 * np.pi * df_feat["DayOfWeek"] / 7.0).round(4)

    return df_feat


def create_lag_features(
    df: pd.DataFrame,
    target_col: str = "Quantity_Sold",
    lags: List[int] = [1, 7, 14, 30],
) -> pd.DataFrame:
    """
    Generate historical demand lag features separately for each medicine.
    Captures yesterday's demand, weekly periodicity, bi-weekly cycles, and monthly baseline.
    """
    df_feat = df.copy()
    
    # Ensure ordered by Medicine and Date
    df_feat = df_feat.sort_values(by=["Medicine", "Date"]).reset_index(drop=True)

    for lag in lags:
        col_name = f"Lag_{lag}"
        df_feat[col_name] = (
            df_feat.groupby("Medicine")[target_col]
            .shift(lag)
        )

    return df_feat


def create_rolling_features(
    df: pd.DataFrame,
    target_col: str = "Quantity_Sold",
) -> pd.DataFrame:
    """
    Generate moving averages and standard deviations using STRICTLY PAST data.
    
    CRITICAL:
    To prevent data leakage, target_col is shifted by 1 before computing
    rolling statistics, ensuring the current day's demand is never observed.
    """
    df_feat = df.copy()
    df_feat = df_feat.sort_values(by=["Medicine", "Date"]).reset_index(drop=True)

    # Shift target by 1 day within each medicine group to strictly prevent leakage
    shifted_target = df_feat.groupby("Medicine")[target_col].shift(1)

    # Rolling means
    df_feat["Rolling_Mean_7"] = (
        shifted_target.groupby(df_feat["Medicine"])
        .rolling(window=7, min_periods=7)
        .mean()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    df_feat["Rolling_Mean_14"] = (
        shifted_target.groupby(df_feat["Medicine"])
        .rolling(window=14, min_periods=14)
        .mean()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    df_feat["Rolling_Mean_30"] = (
        shifted_target.groupby(df_feat["Medicine"])
        .rolling(window=30, min_periods=30)
        .mean()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    # Rolling standard deviations
    df_feat["Rolling_Std_7"] = (
        shifted_target.groupby(df_feat["Medicine"])
        .rolling(window=7, min_periods=7)
        .std()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    df_feat["Rolling_Std_30"] = (
        shifted_target.groupby(df_feat["Medicine"])
        .rolling(window=30, min_periods=30)
        .std()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    return df_feat


def create_domain_and_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create medicine-specific domain interactions:
    - Demand Momentum: short-term trend relative to monthly baseline (Rolling_Mean_7 / Rolling_Mean_30).
    - Local Volatility (CV_7): Rolling_Std_7 / Rolling_Mean_7.
    - Lag Ratio: Ratio of yesterday's demand to weekly moving average.
    - Weather rolling dynamics: past 7-day mean temperature and past 3-day cumulative rainfall.
    - Inventory coverage ratio: estimated days of supply on hand (Stock_Level / Rolling_Mean_7).
    """
    df_feat = df.copy()

    # 1. Demand Momentum & Volatility
    eps = 1e-5
    df_feat["Demand_Momentum_7_30"] = (
        df_feat["Rolling_Mean_7"] / (df_feat["Rolling_Mean_30"] + eps)
    ).round(3)

    df_feat["Demand_Volatility_7"] = (
        df_feat["Rolling_Std_7"] / (df_feat["Rolling_Mean_7"] + eps)
    ).round(3)

    df_feat["Lag1_to_Rolling7_Ratio"] = (
        df_feat["Lag_1"] / (df_feat["Rolling_Mean_7"] + eps)
    ).round(3)

    # 2. Weather rolling dynamics (using past data shift(1))
    shifted_temp = df_feat.groupby("Medicine")["Temperature"].shift(1)
    df_feat["Temp_Rolling_Mean_7"] = (
        shifted_temp.groupby(df_feat["Medicine"])
        .rolling(window=7, min_periods=7)
        .mean()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    shifted_rain = df_feat.groupby("Medicine")["Rainfall"].shift(1)
    df_feat["Rainfall_Rolling_Sum_3"] = (
        shifted_rain.groupby(df_feat["Medicine"])
        .rolling(window=3, min_periods=3)
        .sum()
        .reset_index(level=0, drop=True)
        .round(2)
    )

    # 3. Inventory supply cover days
    df_feat["Stock_Cover_Days"] = (
        df_feat["Stock_Level"] / (df_feat["Rolling_Mean_7"] + eps)
    ).round(2)

    return df_feat


def encode_categorical_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, int]]]:
    """
    Encode categorical features cleanly for ML models:
    - Medicine -> Medicine_Encoded (0 to N-1)
    - Medicine_Category -> Category_Encoded (0 to K-1)
    - Season -> Season_Encoded (ordinal seasonal cycle)
    Preserves original string columns for reporting and interpretability.
    """
    df_feat = df.copy()
    mappings = {}

    # 1. Medicine encoding
    unique_meds = sorted(df_feat["Medicine"].unique())
    med_mapping = {med: idx for idx, med in enumerate(unique_meds)}
    df_feat["Medicine_Encoded"] = df_feat["Medicine"].map(med_mapping)
    mappings["Medicine"] = med_mapping

    # 2. Medicine_Category encoding
    unique_cats = sorted(df_feat["Medicine_Category"].unique())
    cat_mapping = {cat: idx for idx, cat in enumerate(unique_cats)}
    df_feat["Category_Encoded"] = df_feat["Medicine_Category"].map(cat_mapping)
    mappings["Medicine_Category"] = cat_mapping

    # 3. Season encoding (ordered chronologically)
    season_mapping = {
        "Winter": 0,
        "Spring": 1,
        "Summer": 2,
        "Monsoon": 3,
        "Autumn": 4,
    }
    df_feat["Season_Encoded"] = df_feat["Season"].map(season_mapping)
    mappings["Season"] = season_mapping

    return df_feat, mappings


def build_feature_pipeline(
    input_path: str = "dataset/cleaned_medicine_demand.csv",
    output_path: str = "dataset/model_ready_data.csv",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Orchestrate full feature engineering pipeline:
    1. Load sorted cleaned data
    2. Extract calendar & cyclical features
    3. Generate historical demand lags (1, 7, 14, 30)
    4. Generate non-leaking rolling demand features (7, 14, 30)
    5. Compute domain interactions & weather rolling metrics
    6. Encode categorical identifiers
    7. Prune initial 30-day warmup window to ensure zero NaNs
    8. Sort strictly by Date and Medicine without random shuffling
    9. Export model-ready CSV
    """
    raw_df = load_cleaned_dataset(input_path)
    initial_rows = len(raw_df)

    # 1. Calendar
    df_cal = create_calendar_features(raw_df)

    # 2. Lags
    df_lags = create_lag_features(df_cal, target_col="Quantity_Sold", lags=[1, 7, 14, 30])

    # 3. Rolling
    df_roll = create_rolling_features(df_lags, target_col="Quantity_Sold")

    # 4. Domain & Interactions
    df_domain = create_domain_and_interaction_features(df_roll)

    # 5. Categorical encodings
    df_encoded, mappings = encode_categorical_features(df_domain)

    # 6. Trim initial 30-day warmup rows (where 30-day lag/rolling are naturally NaN)
    # This guarantees that all model-ready samples have authentic, complete historical signals.
    df_clean = df_encoded.dropna().reset_index(drop=True)
    trimmed_rows = initial_rows - len(df_clean)

    # Drop redundant raw columns superseded by engineered features
    drop_redundant = ["Day_of_Week", "Is_Weekend"]
    df_clean = df_clean.drop(columns=[c for c in drop_redundant if c in df_clean.columns])

    # Reorder columns logically: Metadata -> Target -> Features
    metadata_cols = ["Date", "Medicine", "Medicine_Category", "Season"]
    target_col = ["Quantity_Sold"]
    feature_columns = [
        # Calendar Features
        "Year", "Month", "Day", "DayOfWeek", "WeekOfYear", "Quarter", "IsWeekend", "Is_Holiday",
        "Month_Sin", "Month_Cos", "DayOfWeek_Sin", "DayOfWeek_Cos",
        # Historical Demand Lags
        "Lag_1", "Lag_7", "Lag_14", "Lag_30",
        # Rolling Statistics (Strictly Past Data)
        "Rolling_Mean_7", "Rolling_Mean_14", "Rolling_Mean_30", "Rolling_Std_7", "Rolling_Std_30",
        # Demand Momentum & Domain Interactions
        "Demand_Momentum_7_30", "Demand_Volatility_7", "Lag1_to_Rolling7_Ratio",
        # Inventory & Pricing Dynamics
        "Stock_Level", "Stock_Cover_Days", "Unit_Price",
        # Weather & Health Outliers
        "Temperature", "Rainfall", "Temp_Rolling_Mean_7", "Rainfall_Rolling_Sum_3", "Is_Demand_Outlier",
        # Categorical Encodings
        "Medicine_Encoded", "Category_Encoded", "Season_Encoded"
    ]
    df_clean = df_clean[metadata_cols + target_col + feature_columns]

    # 7. Maintain strict time-series ordering: Sort by Date, then Medicine (no random shuffling)
    df_clean = df_clean.sort_values(by=["Date", "Medicine"]).reset_index(drop=True)

    # Format Date as clean string for CSV storage
    df_clean["Date"] = df_clean["Date"].dt.strftime("%Y-%m-%d")

    # 8. Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_clean.to_csv(output_path, index=False)

    report = {
        "initial_rows": initial_rows,
        "final_rows": len(df_clean),
        "warmup_rows_trimmed": trimmed_rows,
        "trimmed_percentage": round((trimmed_rows / initial_rows) * 100, 2),
        "total_columns": len(df_clean.columns),
        "num_engineered_features": len(feature_columns),
        "feature_list": feature_columns,
        "mappings": mappings,
        "date_range": f"{df_clean['Date'].min()} to {df_clean['Date'].max()}",
        "medicines_count": df_clean["Medicine"].nunique(),
        "zero_nans_verified": bool(df_clean.isna().sum().sum() == 0),
    }

    return df_clean, report


FEATURE_EXPLANATIONS = {
    # Calendar features
    "Year": "Captures macroeconomic annual secular growth trend (+4.5% year-over-year).",
    "Month": "Captures annual 12-month seasonality patterns.",
    "Day": "Captures within-month pay-cycle dynamics (e.g. salary stocking at start of month).",
    "DayOfWeek": "Captures weekly recurring demand patterns (0=Monday through 6=Sunday).",
    "WeekOfYear": "High-resolution annual epidemiological week (ISO 1 to 52).",
    "Quarter": "Quarterly demand cycle (Q1 to Q4).",
    "IsWeekend": "Binary flag (1 for Sat/Sun, 0 otherwise); distinguishes elevated OTC and first-aid purchases.",
    "Month_Sin": "Sine transform mapping December and January as adjacent months on a unit circle.",
    "Month_Cos": "Cosine transform capturing annual cyclical continuity without jump discontinuities.",
    "DayOfWeek_Sin": "Sine transform representing continuous transition between Sunday and Monday.",
    "DayOfWeek_Cos": "Cosine transform representing weekly circular periodicity.",
    "Is_Holiday": "Binary indicator for national and seasonal festivals impacting clinic hours and purchases.",

    # Historical demand lags
    "Lag_1": "Most recent yesterday's demand; primary short-term autoregressive signal.",
    "Lag_7": "Demand exactly one week ago; captures strong same-day-of-week seasonality.",
    "Lag_14": "Demand two weeks ago; captures bi-weekly recurring patterns.",
    "Lag_30": "Demand thirty days ago; captures monthly recurring refill behaviors.",

    # Rolling demand statistics
    "Rolling_Mean_7": "7-day moving average of strictly past demand; smoothes day-to-day noise.",
    "Rolling_Mean_14": "14-day moving average of strictly past demand; captures medium-term volume.",
    "Rolling_Mean_30": "30-day moving average of strictly past demand; baseline monthly demand anchor.",
    "Rolling_Std_7": "7-day rolling standard deviation; measures short-term demand volatility.",
    "Rolling_Std_30": "30-day rolling standard deviation; measures monthly demand stability/spread.",

    # Interaction & domain features
    "Demand_Momentum_7_30": "Ratio of 7-day to 30-day moving average; detects accelerating vs decelerating demand trends.",
    "Demand_Volatility_7": "Local coefficient of variation (Rolling_Std_7 / Rolling_Mean_7); gauges immediate unpredictability.",
    "Lag1_to_Rolling7_Ratio": "Ratio of yesterday's demand to the weekly mean; detects immediate demand spikes or drop-offs.",
    "Stock_Cover_Days": "Estimated days of inventory remaining (Stock_Level / Rolling_Mean_7) before replenishment is needed.",

    # Weather features
    "Temperature": "Current day ambient temperature in Celsius.",
    "Rainfall": "Current day rainfall volume in mm.",
    "Temp_Rolling_Mean_7": "7-day rolling mean temperature; captures sustained heatwaves or winter cold snaps.",
    "Rainfall_Rolling_Sum_3": "3-day accumulated rainfall; triggers waterborne and monsoon infection spikes.",

    # Inventory and pricing
    "Stock_Level": "Current available inventory units on hand.",
    "Unit_Price": "Unit retail sales price per medicine in currency units.",
    "Is_Demand_Outlier": "Historical flag indicating whether day met statistical surge criteria.",

    # Categorical encodings
    "Medicine_Encoded": "Integer index identifier (0-17) mapping to the specific pharmaceutical drug.",
    "Category_Encoded": "Integer category index (0-11) grouping drugs by therapeutic classification.",
    "Season_Encoded": "Ordinal seasonal index (0=Winter, 1=Spring, 2=Summer, 3=Monsoon, 4=Autumn).",
}


def print_feature_engineering_report(report: Dict[str, Any], output_path: str):
    """Print concise summary of feature engineering pipeline and explanations."""
    print("=" * 70)
    print("MEDICINE DEMAND FEATURE ENGINEERING REPORT")
    print("=" * 70)
    print(f"Model-Ready Dataset Saved: {output_path}")
    print(f"Initial Records:           {report['initial_rows']:,}")
    print(f"Warmup Rows Pruned:        {report['warmup_rows_trimmed']:,} ({report['trimmed_percentage']}%) - initial 30 days")
    print(f"Final Model-Ready Rows:    {report['final_rows']:,}")
    print(f"Number of Medicines:       {report['medicines_count']}")
    print(f"Effective Date Range:      {report['date_range']}")
    print(f"Zero NaNs Verified:        {report['zero_nans_verified']}")
    print(f"Engineered Features Count: {report['num_engineered_features']}")
    print("-" * 70)
    print(f"{'FEATURE NAME':<26} | {'PURPOSE & DESCRIPTION'}")
    print("-" * 70)

    for feat in report["feature_list"]:
        desc = FEATURE_EXPLANATIONS.get(feat, "Engineered model input feature.")
        print(f"{feat:<26} | {desc}")

    print("=" * 70)


if __name__ == "__main__":
    in_path = os.path.join("dataset", "cleaned_medicine_demand.csv")
    out_path = os.path.join("dataset", "model_ready_data.csv")
    _, summary = build_feature_pipeline(in_path, out_path)
    print_feature_engineering_report(summary, out_path)
