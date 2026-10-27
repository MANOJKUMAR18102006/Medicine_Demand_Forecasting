"""
Inference & Multi-Horizon Recursive Demand Forecasting Module.

Loads the trained best model and preprocessing artifacts, generates future calendar signals,
and performs recursive multi-step forecasting (7, 14, 30 days) for any selected medicine.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import joblib

from ml.data_preprocessing import load_dataset
from dataset.generate_dataset import get_season, generate_holiday_calendar


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_MODELS_DIR = os.path.join(PROJECT_ROOT, "ml", "models")
DEFAULT_DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "cleaned_medicine_demand.csv")


class MedicineDemandForecaster:
    """
    Production inference engine that handles recursive feature generation
    and model execution for multi-horizon medicine demand forecasting.
    """

    def __init__(
        self,
        models_dir: str = DEFAULT_MODELS_DIR,
        dataset_path: str = DEFAULT_DATASET_PATH,
    ):
        self.models_dir = models_dir
        self.dataset_path = dataset_path
        self._load_artifacts()
        self._load_latest_history()

    def _load_artifacts(self):
        """Load best trained model, preprocessing metadata, and feature schema."""
        best_model_path = os.path.join(self.models_dir, "best_model.pkl")
        prep_path = os.path.join(self.models_dir, "preprocessing.pkl")

        if not os.path.exists(best_model_path) or not os.path.exists(prep_path):
            raise FileNotFoundError(
                f"Model artifacts missing in {self.models_dir}. Ensure train_model.py and evaluate_model.py have been executed."
            )

        self.model = joblib.load(best_model_path)
        self.prep = joblib.load(prep_path)
        self.feature_columns = self.prep["feature_columns"]
        self.medicine_mapping = self.prep["medicine_mapping"]
        self.category_mapping = self.prep["category_mapping"]
        self.season_mapping = self.prep["season_mapping"]
        self.available_medicines = self.prep["medicines"]

    def _load_latest_history(self):
        """Cache the most recent 60 days of historical demand per medicine for recursive lags."""
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Cleaned dataset missing at {self.dataset_path}")
        df = pd.read_csv(self.dataset_path)
        df["Date"] = pd.to_datetime(df["Date"])
        self.history_df = df.sort_values(by=["Medicine", "Date"]).reset_index(drop=True)
        self.last_historical_date = self.history_df["Date"].max()

    def forecast(
        self,
        medicine: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Execute recursive multi-step forecasting for a specified medicine over `days` ahead.
        
        Guarantees:
        - Future dates are strictly projected starting from day after last historical record.
        - Step-by-step recursive lag and rolling updates: step k uses predictions from k-1, k-7, etc.
        - Strictly zero future lookahead or target leakage.
        """
        base_medicine = medicine
        if base_medicine not in self.medicine_mapping:
            for m in self.available_medicines:
                if m.lower() == medicine.lower():
                    base_medicine = m
                    break
            else:
                for m in self.available_medicines:
                    if m.lower() in medicine.lower():
                        base_medicine = m
                        break
                else:
                    raise ValueError(
                        f"Medicine '{medicine}' not recognized. Available: {', '.join(self.available_medicines)}"
                    )

        if days not in [7, 14, 30]:
            # Accept any positive integer up to 60 for flexibility, but default valid values are 7, 14, 30
            if days <= 0 or days > 60:
                raise ValueError(f"Forecast horizon must be between 1 and 60 days (standard: 7, 14, 30). Received: {days}")

        # Extract historical records for this medicine
        med_history = self.history_df[self.history_df["Medicine"] == base_medicine].sort_values("Date")
        category = med_history["Medicine_Category"].iloc[-1]
        unit_price = float(med_history["Unit_Price"].iloc[-1])
        last_stock = float(med_history["Stock_Level"].iloc[-1])
        
        # Prepare historical sequence of quantities sold (chronological list)
        history_demands = med_history["Quantity_Sold"].tolist()
        history_temps = med_history["Temperature"].tolist()
        history_rains = med_history["Rainfall"].tolist()

        start_forecast_date = self.last_historical_date + timedelta(days=1)
        end_forecast_date = self.last_historical_date + timedelta(days=days)
        holidays_set = generate_holiday_calendar(start_forecast_date, end_forecast_date)

        forecast_results = []
        eps = 1e-5

        current_date = start_forecast_date
        for step in range(days):
            date_str = current_date.strftime("%Y-%m-%d")
            month = current_date.month
            day = current_date.day
            year = current_date.year
            day_of_week = current_date.weekday()
            week_of_year = int(current_date.isocalendar().week)
            quarter = (month - 1) // 3 + 1
            is_weekend = int(day_of_week >= 5)
            is_holiday = int(date_str in holidays_set)
            season_name = get_season(month)

            # Cyclical trigonometric transforms
            month_sin = round(np.sin(2 * np.pi * month / 12.0), 4)
            month_cos = round(np.cos(2 * np.pi * month / 12.0), 4)
            dow_sin = round(np.sin(2 * np.pi * day_of_week / 7.0), 4)
            dow_cos = round(np.cos(2 * np.pi * day_of_week / 7.0), 4)

            # Recursive Lags from history + prior predictions
            lag_1 = float(history_demands[-1])
            lag_7 = float(history_demands[-7]) if len(history_demands) >= 7 else lag_1
            lag_14 = float(history_demands[-14]) if len(history_demands) >= 14 else lag_1
            lag_30 = float(history_demands[-30]) if len(history_demands) >= 30 else lag_1

            # Recursive Rolling Statistics (last 7, 14, 30 prior values)
            past_7 = history_demands[-7:]
            past_14 = history_demands[-14:]
            past_30 = history_demands[-30:]

            rolling_mean_7 = round(float(np.mean(past_7)), 2)
            rolling_mean_14 = round(float(np.mean(past_14)), 2)
            rolling_mean_30 = round(float(np.mean(past_30)), 2)
            rolling_std_7 = round(float(np.std(past_7, ddof=1) if len(past_7) > 1 else 0.0), 2)
            rolling_std_30 = round(float(np.std(past_30, ddof=1) if len(past_30) > 1 else 0.0), 2)

            # Interaction & Ratios
            demand_momentum_7_30 = round(rolling_mean_7 / (rolling_mean_30 + eps), 3)
            demand_volatility_7 = round(rolling_std_7 / (rolling_mean_7 + eps), 3)
            lag1_to_rolling7 = round(lag_1 / (rolling_mean_7 + eps), 3)

            # Weather estimates (projected seasonal baseline for temperature and rainfall)
            day_of_year = current_date.timetuple().tm_yday
            radians = 2 * np.pi * (day_of_year - 145) / 365.0
            expected_temp = round(float(26.0 + 9.0 * np.cos(radians)), 1)
            expected_rain = 12.0 if season_name == "Monsoon" else 1.0

            history_temps.append(expected_temp)
            history_rains.append(expected_rain)
            temp_rolling_7 = round(float(np.mean(history_temps[-7:])), 2)
            rain_rolling_3 = round(float(np.sum(history_rains[-3:])), 2)

            # Inventory cover proxy
            stock_cover_days = round(last_stock / (rolling_mean_7 + eps), 2)

            # Categorical encodings
            med_encoded = self.medicine_mapping[base_medicine]
            cat_encoded = self.category_mapping.get(category, 0)
            season_encoded = self.season_mapping.get(season_name, 0)

            # Construct feature vector matching exact training order
            row_dict = {
                "Year": year,
                "Month": month,
                "Day": day,
                "DayOfWeek": day_of_week,
                "WeekOfYear": week_of_year,
                "Quarter": quarter,
                "IsWeekend": is_weekend,
                "Is_Holiday": is_holiday,
                "Month_Sin": month_sin,
                "Month_Cos": month_cos,
                "DayOfWeek_Sin": dow_sin,
                "DayOfWeek_Cos": dow_cos,
                "Lag_1": lag_1,
                "Lag_7": lag_7,
                "Lag_14": lag_14,
                "Lag_30": lag_30,
                "Rolling_Mean_7": rolling_mean_7,
                "Rolling_Mean_14": rolling_mean_14,
                "Rolling_Mean_30": rolling_mean_30,
                "Rolling_Std_7": rolling_std_7,
                "Rolling_Std_30": rolling_std_30,
                "Demand_Momentum_7_30": demand_momentum_7_30,
                "Demand_Volatility_7": demand_volatility_7,
                "Lag1_to_Rolling7_Ratio": lag1_to_rolling7,
                "Stock_Level": last_stock,
                "Stock_Cover_Days": stock_cover_days,
                "Unit_Price": unit_price,
                "Temperature": expected_temp,
                "Rainfall": expected_rain,
                "Temp_Rolling_Mean_7": temp_rolling_7,
                "Rainfall_Rolling_Sum_3": rain_rolling_3,
                "Is_Demand_Outlier": 0,
                "Medicine_Encoded": med_encoded,
                "Category_Encoded": cat_encoded,
                "Season_Encoded": season_encoded,
            }

            feature_vector = np.array([[row_dict[col] for col in self.feature_columns]])

            # Model prediction
            raw_pred = float(self.model.predict(feature_vector)[0])
            predicted_qty = max(0, int(round(raw_pred)))

            # Append to predicted results
            forecast_results.append({
                "date": date_str,
                "predicted_demand": predicted_qty,
            })

            # Append predicted quantity to historical sequence for subsequent step recursive lags
            history_demands.append(predicted_qty)

            # Step forward to next calendar day
            current_date += timedelta(days=1)

        total_demand = sum(item["predicted_demand"] for item in forecast_results)
        avg_demand = round(total_demand / len(forecast_results), 1)

        return {
            "medicine": medicine,
            "days": days,
            "forecast": forecast_results,
            "total_predicted_demand": total_demand,
            "average_daily_demand": avg_demand,
            "category": category,
            "unit_price": unit_price,
            "model_used": type(self.model).__name__,
            "forecast_start": forecast_results[0]["date"],
            "forecast_end": forecast_results[-1]["date"],
        }


# Singleton forecaster instance for reuse across backend and scripts
_FORECASTER_INSTANCE: Optional[MedicineDemandForecaster] = None


def get_forecaster() -> MedicineDemandForecaster:
    """Retrieve or initialize singleton forecaster."""
    global _FORECASTER_INSTANCE
    if _FORECASTER_INSTANCE is None:
        _FORECASTER_INSTANCE = MedicineDemandForecaster()
    return _FORECASTER_INSTANCE


def forecast_demand(medicine: str, days: int = 7) -> Dict[str, Any]:
    """
    Main reusable forecasting API function.
    Supports 7, 14, and 30-day horizons.
    """
    forecaster = get_forecaster()
    return forecaster.forecast(medicine, days)


if __name__ == "__main__":
    sample_med = "Paracetamol"
    for horizon in [7, 14, 30]:
        res = forecast_demand(sample_med, horizon)
        print(f"\n{sample_med} {horizon}-Day Forecast ({res['forecast_start']} to {res['forecast_end']}):")
        print(f"Total Predicted Demand: {res['total_predicted_demand']} units (Avg: {res['average_daily_demand']}/day)")
        print(f"First 3 days: {res['forecast'][:3]}")
