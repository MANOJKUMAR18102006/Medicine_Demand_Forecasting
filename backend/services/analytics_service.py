"""
Analytics Service calculating dataset-wide KPIs, alerts, trends, and model performance.
"""

import os
import json
from typing import Dict, Any, List
import pandas as pd
from ml.inventory_optimizer import analyze_inventory


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DATASET_PATH = os.path.join(PROJECT_ROOT, "dataset", "cleaned_medicine_demand.csv")
DEFAULT_METRICS_PATH = os.path.join(PROJECT_ROOT, "ml", "models", "model_metrics.json")


class AnalyticsService:
    """Service to aggregate dashboard analytics, stock alerts, and model evaluation metrics."""

    def __init__(
        self,
        dataset_path: str = DEFAULT_DATASET_PATH,
        metrics_json_path: str = DEFAULT_METRICS_PATH,
    ):
        self.dataset_path = dataset_path
        self.metrics_json_path = metrics_json_path
        self._summary_cache = None

    def get_model_metrics(self) -> Dict[str, Any]:
        """Load evaluation comparison metrics and best model summary."""
        if not os.path.exists(self.metrics_json_path):
            raise FileNotFoundError(f"Model metrics file missing at {self.metrics_json_path}")
        with open(self.metrics_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_dashboard_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Compute live summary metrics, monthly trends, and inventory alerts with caching."""
        if self._summary_cache is not None and not force_refresh:
            return self._summary_cache

        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset missing at {self.dataset_path}")

        df = pd.read_csv(self.dataset_path)

        total_medicines = int(df["Medicine"].nunique())
        total_records = len(df)
        avg_demand = round(float(df["Quantity_Sold"].mean()), 1)

        # Medicine-wise demand summary
        med_summary = (
            df.groupby(["Medicine", "Medicine_Category"])
            .agg(
                total_demand=("Quantity_Sold", "sum"),
                avg_daily_demand=("Quantity_Sold", "mean"),
                std_demand=("Quantity_Sold", "std"),
                stock_level=("Stock_Level", "last"),
            )
            .reset_index()
        )
        med_summary["cv"] = (med_summary["std_demand"] / med_summary["avg_daily_demand"]).round(3)
        med_summary = med_summary.sort_values(by="total_demand", ascending=False).reset_index(drop=True)

        highest_demand_medicine = med_summary.iloc[0]["Medicine"]

        # Top 10 medicines list
        top_meds_list = [
            {
                "medicine": row["Medicine"],
                "category": row["Medicine_Category"],
                "total_demand": int(row["total_demand"]),
                "avg_daily_demand": round(float(row["avg_daily_demand"]), 1),
                "cv": float(row["cv"]),
                "stock_level": int(row["stock_level"]),
            }
            for _, row in med_summary.head(10).iterrows()
        ]

        all_meds_list = [
            {
                "medicine": row["Medicine"],
                "category": row["Medicine_Category"],
                "total_demand": int(row["total_demand"]),
                "avg_daily_demand": round(float(row["avg_daily_demand"]), 1),
                "cv": float(row["cv"]),
                "stock_level": int(row["stock_level"]),
            }
            for _, row in med_summary.iterrows()
        ]

        # Monthly trends
        month_order = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        monthly_df = (
            df.groupby("Month")
            .agg(
                avg_demand=("Quantity_Sold", "mean"),
                total_demand=("Quantity_Sold", "sum"),
            )
            .reindex(month_order)
            .reset_index()
        )
        monthly_summary = [
            {
                "month": r["Month"][:3],  # Jan, Feb...
                "avg_demand": round(float(r["avg_demand"]), 1),
                "total_demand": int(r["total_demand"]),
            }
            for _, r in monthly_df.iterrows()
        ]

        # Compute inventory alerts across all 18 medicines using 7-day forecast
        alerts = []
        low_count = 0
        crit_count = 0
        suff_count = 0

        for med in med_summary["Medicine"]:
            try:
                inv = analyze_inventory(medicine=med, days=7)
                alerts.append({
                    "medicine": inv["medicine"],
                    "category": inv["category"],
                    "current_stock": inv["current_stock"],
                    "predicted_demand": inv["predicted_demand"],
                    "safety_stock": inv["safety_stock"],
                    "required_stock": inv["required_stock"],
                    "expected_shortage": inv["expected_shortage"],
                    "status": inv["inventory_status"],
                    "recommended_order": inv["recommended_order_quantity"],
                })
                if inv["inventory_status"] == "Critical":
                    crit_count += 1
                elif inv["inventory_status"] == "Low Stock":
                    low_count += 1
                else:
                    suff_count += 1
            except Exception:
                pass

        # Sort alerts: Critical first, then Low Stock, then others
        status_priority = {"Critical": 0, "Low Stock": 1, "Sufficient": 2, "Overstocked": 3}
        alerts.sort(key=lambda a: (status_priority.get(a["status"], 9), -a["expected_shortage"]))

        result = {
            "total_medicines": total_medicines,
            "total_historical_records": total_records,
            "average_demand": avg_demand,
            "highest_demand_medicine": highest_demand_medicine,
            "low_stock_count": low_count,
            "critical_stock_count": crit_count,
            "sufficient_stock_count": suff_count,
            "monthly_demand_summary": monthly_summary,
            "medicine_wise_demand_summary": all_meds_list,
            "inventory_alerts": alerts,
            "top_medicines": top_meds_list,
        }
        self._summary_cache = result
        return result
