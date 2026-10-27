"""
Data Preprocessing Module for Medicine Demand Forecasting.

Handles ingestion, inspection, sorting, deduplication, missing value treatment,
non-destructive outlier detection, and daily continuity validation for historical
medicine consumption datasets.
"""

import os
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load medicine demand dataset from CSV and convert Date column to datetime.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")
    
    df = pd.read_csv(file_path)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def inspect_dataset(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Inspect dataset schema, shape, data types, and summary statistics.
    """
    info = {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "summary": df.describe().to_dict(),
    }
    return info


def sort_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort records chronologically by Medicine and Date.
    """
    return df.sort_values(by=["Medicine", "Date"]).reset_index(drop=True)


def detect_missing_values(df: pd.DataFrame) -> pd.Series:
    """
    Count missing values across all columns.
    """
    return df.isnull().sum()


def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values appropriately per medicine group:
    - Numerical time-series metrics: forward-fill then backward-fill within each medicine group.
    - Weather/environment: median by month/season.
    """
    df_cleaned = df.copy()
    if df_cleaned.isnull().values.any():
        numeric_cols = ["Quantity_Sold", "Stock_Level", "Unit_Price"]
        for col in numeric_cols:
            if col in df_cleaned.columns and df_cleaned[col].isnull().any():
                df_cleaned[col] = (
                    df_cleaned.groupby("Medicine")[col]
                    .transform(lambda grp: grp.ffill().bfill().fillna(0))
                )

        weather_cols = ["Temperature", "Rainfall"]
        for col in weather_cols:
            if col in df_cleaned.columns and df_cleaned[col].isnull().any():
                df_cleaned[col] = (
                    df_cleaned.groupby("Month")[col]
                    .transform(lambda grp: grp.fillna(grp.median()))
                )

    return df_cleaned


def detect_and_remove_duplicates(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Detect and deduplicate identical (Date, Medicine) records, retaining the first occurrence.
    """
    duplicate_count = int(df.duplicated(subset=["Date", "Medicine"]).sum())
    if duplicate_count > 0:
        df_dedup = df.drop_duplicates(subset=["Date", "Medicine"], keep="first").reset_index(drop=True)
    else:
        df_dedup = df.copy()
    return df_dedup, duplicate_count


def validate_and_correct_numeric_bounds(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Check for impossible negative values in Quantity_Sold and Stock_Level.
    Clips negatives to 0 to prevent downstream modeling errors.
    """
    df_bounded = df.copy()
    invalid_counts = {
        "negative_quantity_sold": int((df_bounded["Quantity_Sold"] < 0).sum()),
        "negative_stock_level": int((df_bounded["Stock_Level"] < 0).sum()),
    }

    if invalid_counts["negative_quantity_sold"] > 0:
        df_bounded["Quantity_Sold"] = df_bounded["Quantity_Sold"].clip(lower=0)

    if invalid_counts["negative_stock_level"] > 0:
        df_bounded["Stock_Level"] = df_bounded["Stock_Level"].clip(lower=0)

    return df_bounded, invalid_counts


def detect_demand_outliers(
    df: pd.DataFrame, iqr_multiplier: float = 1.5
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Detect statistical outliers in Quantity_Sold on a per-medicine basis using IQR.
    Note: Outliers are tagged (Is_Demand_Outlier) but PRESERVED to retain legitimate
    demand surges (e.g., epidemic waves, seasonal outbreaks, bulk orders).
    """
    df_flagged = df.copy()
    df_flagged["Is_Demand_Outlier"] = 0

    outlier_stats = {}
    total_outliers = 0

    for medicine, group in df_flagged.groupby("Medicine"):
        q1 = group["Quantity_Sold"].quantile(0.25)
        q3 = group["Quantity_Sold"].quantile(0.75)
        iqr = q3 - q1
        upper_bound = q3 + (iqr_multiplier * iqr)
        lower_bound = max(0, q1 - (iqr_multiplier * iqr))

        outlier_mask = (df_flagged["Medicine"] == medicine) & (
            (df_flagged["Quantity_Sold"] > upper_bound) | (df_flagged["Quantity_Sold"] < lower_bound)
        )
        count = int(outlier_mask.sum())
        total_outliers += count
        df_flagged.loc[outlier_mask, "Is_Demand_Outlier"] = 1

        outlier_stats[medicine] = {
            "q1": round(float(q1), 1),
            "q3": round(float(q3), 1),
            "upper_bound": round(float(upper_bound), 1),
            "outlier_count": count,
            "max_observed": int(group["Quantity_Sold"].max()),
        }

    summary = {
        "total_outliers_flagged": total_outliers,
        "outlier_percentage": round((total_outliers / len(df_flagged)) * 100, 2),
        "per_medicine": outlier_stats,
    }
    return df_flagged, summary


def validate_continuous_daily_records(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify that each medicine has continuous daily records without date gaps.
    """
    continuity_report = {}
    all_continuous = True

    for medicine, group in df.groupby("Medicine"):
        dates = group["Date"].sort_values()
        expected_range = pd.date_range(start=dates.min(), end=dates.max(), freq="D")
        actual_dates_set = set(dates.dt.strftime("%Y-%m-%d"))
        expected_dates_set = set(expected_range.strftime("%Y-%m-%d"))

        missing_dates = expected_dates_set - actual_dates_set
        is_continuous = len(missing_dates) == 0

        if not is_continuous:
            all_continuous = False

        continuity_report[medicine] = {
            "total_days": len(dates),
            "expected_days": len(expected_range),
            "is_continuous": is_continuous,
            "missing_dates_count": len(missing_dates),
        }

    return {
        "all_continuous": all_continuous,
        "details": continuity_report,
    }


def preprocess_medicine_data(
    input_path: str = "dataset/medicine_demand.csv",
    output_path: str = "dataset/cleaned_medicine_demand.csv",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Execute end-to-end data preprocessing pipeline:
    1. Load raw dataset
    2. Convert Date to datetime
    3. Sort records by Medicine and Date
    4. Detect & handle missing values
    5. Deduplicate records
    6. Validate non-negative bounds
    7. Detect & flag demand outliers non-destructively
    8. Validate daily frequency continuity
    9. Export cleaned dataset to CSV
    """
    # 1. Load dataset
    raw_df = load_dataset(input_path)
    original_row_count = len(raw_df)

    # 2. Inspect initial nulls
    initial_missing = detect_missing_values(raw_df)

    # 3. Sort chronologically
    sorted_df = sort_records(raw_df)

    # 4. Handle missing values
    filled_df = handle_missing_values(sorted_df)

    # 5. Detect and remove duplicates
    dedup_df, dup_count = detect_and_remove_duplicates(filled_df)

    # 6. Validate bounds (Quantity_Sold & Stock_Level >= 0)
    bounded_df, bounds_report = validate_and_correct_numeric_bounds(dedup_df)

    # 7. Detect outliers non-destructively
    cleaned_df, outlier_info = detect_demand_outliers(bounded_df)

    # 8. Check daily continuity
    continuity_info = validate_continuous_daily_records(cleaned_df)

    final_row_count = len(cleaned_df)

    # 9. Format Date back to ISO string for clean CSV serialization
    export_df = cleaned_df.copy()
    export_df["Date"] = export_df["Date"].dt.strftime("%Y-%m-%d")

    # Ensure target directory exists and save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    export_df.to_csv(output_path, index=False)

    report = {
        "original_row_count": original_row_count,
        "final_row_count": final_row_count,
        "missing_values": initial_missing.to_dict(),
        "duplicate_count": dup_count,
        "negative_bounds_corrected": bounds_report,
        "outlier_information": outlier_info,
        "date_range": f"{cleaned_df['Date'].min().strftime('%Y-%m-%d')} to {cleaned_df['Date'].max().strftime('%Y-%m-%d')}",
        "total_calendar_days": (cleaned_df["Date"].max() - cleaned_df["Date"].min()).days + 1,
        "number_of_medicines": cleaned_df["Medicine"].nunique(),
        "daily_continuity_passed": continuity_info["all_continuous"],
    }

    return export_df, report


def print_preprocessing_report(report: Dict[str, Any], output_path: str):
    """
    Print concise, structured preprocessing report.
    """
    print("=" * 65)
    print("MEDICINE DEMAND PREPROCESSING REPORT")
    print("=" * 65)
    print(f"Cleaned Dataset Saved To:  {output_path}")
    print(f"Original Row Count:        {report['original_row_count']:,}")
    print(f"Final Row Count:           {report['final_row_count']:,}")
    print(f"Number of Medicines:       {report['number_of_medicines']}")
    print(f"Date Range:                {report['date_range']} ({report['total_calendar_days']} days)")
    print(f"Duplicate Records Found:   {report['duplicate_count']}")
    print(f"Negative Values Corrected: Qty={report['negative_bounds_corrected']['negative_quantity_sold']}, Stock={report['negative_bounds_corrected']['negative_stock_level']}")
    print(f"Daily Continuity Valid:    {'YES (100% complete)' if report['daily_continuity_passed'] else 'NO (gaps detected)'}")
    print("-" * 65)
    print("MISSING VALUES AUDIT:")
    for col, count in report["missing_values"].items():
        print(f" - {col:<22}: {count}")
    print("-" * 65)
    outlier_summary = report["outlier_information"]
    print(f"OUTLIER DETECTION (Non-Destructive IQR Flagging):")
    print(f" - Total Demand Outliers Flagged: {outlier_summary['total_outliers_flagged']:,} ({outlier_summary['outlier_percentage']}%)")
    print(f" - Policy: Preserved in dataset (tagged as 'Is_Demand_Outlier')")
    print("   to retain legitimate epidemiological surges and demand spikes.")
    print("-" * 65)
    print("SAMPLE PER-MEDICINE OUTLIER SPREAD:")
    sample_meds = list(outlier_summary["per_medicine"].keys())[:6]
    for med in sample_meds:
        m = outlier_summary["per_medicine"][med]
        print(f" - {med:<15}: Upper Threshold={m['upper_bound']:<5.1f} | Flagged={m['outlier_count']:<3} | Peak Observed={m['max_observed']}")
    print("=" * 65)


if __name__ == "__main__":
    in_file = os.path.join("dataset", "medicine_demand.csv")
    out_file = os.path.join("dataset", "cleaned_medicine_demand.csv")
    _, summary_report = preprocess_medicine_data(in_file, out_file)
    print_preprocessing_report(summary_report, out_file)
