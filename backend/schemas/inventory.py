"""
Pydantic validation schemas for Inventory Analysis.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.schemas.forecast import ForecastItem


class InventoryAnalysisRequest(BaseModel):
    medicine: str = Field(..., description="Medicine name", example="Paracetamol")
    days: int = Field(default=7, description="Forecast period in days", example=7)
    current_stock: Optional[int] = Field(default=None, ge=0, description="Available stock units on hand", example=900)


class InventoryAnalysisResponse(BaseModel):
    medicine: str
    forecast_period: int
    predicted_demand: int
    current_stock: int
    safety_stock: int
    required_stock: int
    expected_shortage: int
    recommended_order_quantity: int
    inventory_status: str
    recommendation: str
    average_daily_demand: float
    category: str
    unit_price: float
    forecast_timeline: List[ForecastItem]
    can_exchange: Optional[bool] = False
    can_buy: Optional[bool] = False
    surplus_shops_count: Optional[int] = 0
    suppliers_count: Optional[int] = 0
    replenishment_message: Optional[str] = None
