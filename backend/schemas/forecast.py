"""
Pydantic validation schemas for Demand Forecasting.
"""

from typing import List
from pydantic import BaseModel, Field


class ForecastItem(BaseModel):
    date: str
    predicted_demand: int


class ForecastRequest(BaseModel):
    medicine: str = Field(..., description="Medicine brand or generic name", example="Paracetamol")
    days: int = Field(default=7, description="Forecast horizon in days (7, 14, or 30)", example=7)


class ForecastResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    medicine: str
    days: int
    forecast: List[ForecastItem]
    total_predicted_demand: int
    average_daily_demand: float
    category: str
    unit_price: float
    model_used: str
    forecast_start: str
    forecast_end: str
