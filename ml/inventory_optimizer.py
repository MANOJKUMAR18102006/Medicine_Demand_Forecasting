"""
Inventory Analysis & Procurement Decision-Support Module.

Combines machine-learning demand forecasts, current stock levels, and safety buffer formulas
to determine inventory health, stock shortages, and recommended reorder quantities.
"""

import os
import sys
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import numpy as np
from ml.predict import forecast_demand


# Standard Lead Times in days and Service Level factor (Z=1.65 for 95% availability)
DEFAULT_LEAD_TIME_DAYS = 2
SERVICE_FACTOR_95_PCT = 1.65


def calculate_safety_stock(
    daily_demand_std: float,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
    z_score: float = SERVICE_FACTOR_95_PCT,
    min_safety_stock: int = 20,
) -> int:
    """
    Transparent Classical Safety Stock Formula:
    SS = Z * sigma_demand * sqrt(Lead_Time)
    Ensures minimum threshold to handle demand surges.
    """
    safety_stock = z_score * daily_demand_std * np.sqrt(lead_time_days)
    return max(min_safety_stock, int(round(safety_stock)))


def classify_inventory_status(
    current_stock: int,
    forecasted_demand: int,
    safety_stock: int,
    required_stock: int,
) -> str:
    """
    Transparent Inventory Status Classification:
    - Critical: Current stock covers less than 50% of forecast or is below safety stock.
    - Low Stock: Current stock is below required stock (shortage exists).
    - Sufficient: Current stock adequately covers required stock up to 2x buffer.
    - Overstocked: Current stock exceeds 2x the required stock.
    """
    if current_stock < (0.5 * forecasted_demand) or current_stock < safety_stock:
        return "Critical"
    elif current_stock < required_stock:
        return "Low Stock"
    elif current_stock <= (2.0 * required_stock):
        return "Sufficient"
    else:
        return "Overstocked"


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "cleaned_medicine_demand.csv")


def analyze_inventory(
    medicine: str,
    days: int = 7,
    current_stock: Optional[int] = None,
    dataset_path: str = DEFAULT_DATASET_PATH,
) -> Dict[str, Any]:
    """
    Execute full inventory decision-support analysis for a medicine over a forecast period.
    
    Parameters:
    - medicine: Name of the medicine (e.g. "Paracetamol")
    - days: Forecast period in days (7, 14, 30)
    - current_stock: Available inventory units on hand. If None, uses last recorded historical stock.
    
    Formulas:
    - Forecasted Demand = sum(daily_predicted_demand)
    - Safety Stock = max(20, round(1.65 * std_daily_demand * sqrt(Lead_Time)))
    - Required Stock = Forecasted Demand + Safety Stock
    - Expected Shortage = max(0, Required Stock - Current Stock)
    - Recommended Order Quantity = max(0, Required Stock - Current Stock)
    """
    # 1. Run ML demand forecasting
    forecast_result = forecast_demand(medicine, days)
    predicted_demand = int(forecast_result["total_predicted_demand"])

    # 2. Determine historical demand variability for safety stock
    df = pd.read_csv(dataset_path)
    med_df = df[df["Medicine"] == medicine]
    if len(med_df) > 0:
        std_demand = float(med_df["Quantity_Sold"].std())
        last_recorded_stock = int(med_df["Stock_Level"].iloc[-1])
    else:
        std_demand = 25.0
        last_recorded_stock = 500

    if current_stock is None or current_stock < 0:
        current_stock = last_recorded_stock

    # 3. Calculate Safety Stock & Required Stock
    safety_stock = calculate_safety_stock(std_demand, lead_time_days=DEFAULT_LEAD_TIME_DAYS)
    required_stock = predicted_demand + safety_stock

    # 4. Calculate Shortage & Order Recommendation
    expected_shortage = max(0, required_stock - current_stock)
    recommended_order_quantity = max(0, required_stock - current_stock)

    # 5. Classify Inventory Status
    status = classify_inventory_status(
        current_stock, predicted_demand, safety_stock, required_stock
    )

    # 6. Actionable Recommendation Message
    if status == "Critical":
        recommendation = f"Recommended Order: {recommended_order_quantity:,} units immediately. Critical stock depletion risk within {days} days."
    elif status == "Low Stock":
        recommendation = f"Recommended Order: {recommended_order_quantity:,} units to restore required safety buffer."
    elif status == "Sufficient":
        recommendation = f"No immediate reorder needed. Current stock ({current_stock:,} units) covers {days}-day demand and safety buffer."
    else:
        recommendation = f"Overstocked. Current inventory ({current_stock:,} units) exceeds 200% of required stock. Delay replenishments."

    return {
        "medicine": medicine,
        "forecast_period": days,
        "predicted_demand": predicted_demand,
        "current_stock": current_stock,
        "safety_stock": safety_stock,
        "required_stock": required_stock,
        "expected_shortage": expected_shortage,
        "recommended_order_quantity": recommended_order_quantity,
        "inventory_status": status,
        "recommendation": recommendation,
        "average_daily_demand": forecast_result["average_daily_demand"],
        "category": forecast_result["category"],
        "unit_price": forecast_result["unit_price"],
        "forecast_timeline": forecast_result["forecast"],
    }


if __name__ == "__main__":
    test_med = "Paracetamol"
    test_cases = [
        (test_med, 7, 500),    # Critical / Low
        (test_med, 7, 1800),   # Sufficient
        (test_med, 7, 4500),   # Overstocked
    ]

    print("=" * 65)
    print("PHASE 8: INVENTORY ANALYSIS TEST CASES")
    print("=" * 65)
    for med, period, stock in test_cases:
        res = analyze_inventory(med, period, stock)
        print(f"\nMedicine: {res['medicine']} | Period: {res['forecast_period']} Days | Current Stock: {res['current_stock']}")
        print(f"Predicted Demand: {res['predicted_demand']} | Safety Stock: {res['safety_stock']} | Required Stock: {res['required_stock']}")
        print(f"Shortage: {res['expected_shortage']} | Order Qty: {res['recommended_order_quantity']} | Status: {res['inventory_status']}")
        print(f"Advice: {res['recommendation']}")
    print("=" * 65)
