"""
Pydantic schemas for Analytics and Model Metrics.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ModelMetricItem(BaseModel):
    model: str
    mae: float
    rmse: float
    r2: float
    mape: float


class BestModelSummary(BaseModel):
    model_config = {"protected_namespaces": ()}

    model_name: str
    mae: float
    rmse: float
    r2: float
    mape: float


class ModelMetricsResponse(BaseModel):
    comparison: List[ModelMetricItem]
    best_model: BestModelSummary
    evaluation_period: Optional[Dict[str, Any]] = None


class InventoryAlertItem(BaseModel):
    medicine: str
    category: str
    current_stock: int
    predicted_demand: int
    safety_stock: int
    required_stock: int
    expected_shortage: int
    status: str
    recommended_order: int


class MonthlyTrendItem(BaseModel):
    month: str
    avg_demand: float
    total_demand: int


class MedicineDemandSummaryItem(BaseModel):
    medicine: str
    category: str
    total_demand: int
    avg_daily_demand: float
    cv: float
    stock_level: int


class AnalyticsSummaryResponse(BaseModel):
    total_medicines: int
    total_historical_records: int
    average_demand: float
    highest_demand_medicine: str
    low_stock_count: int
    critical_stock_count: int
    sufficient_stock_count: int
    monthly_demand_summary: List[MonthlyTrendItem]
    medicine_wise_demand_summary: List[MedicineDemandSummaryItem]
    inventory_alerts: List[InventoryAlertItem]
    top_medicines: List[MedicineDemandSummaryItem]
