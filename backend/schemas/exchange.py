"""
Pydantic Schemas for Nearby Medical Shop Stock Exchange.
"""

from typing import Optional
from pydantic import BaseModel, Field


class ExchangeSurplusShopResponse(BaseModel):
    shop_id: str
    shop_name: str
    owner_name: str
    phone_number: str
    address: str
    city: Optional[str] = None
    distance_km: Optional[float] = None
    medicine_name: str
    category: str
    current_stock: int
    safety_stock: int
    projected_7d_demand: int
    reserved_stock: int
    available_surplus: int
    unit_of_measurement: str = "units"
    unit_price: float = 0.0
    expiry_date: Optional[str] = None


class ExchangeRequestCreate(BaseModel):
    supplying_shop_id: str = Field(..., min_length=1, description="Target medical shop ID with surplus stock")
    medicine_name: str = Field(..., min_length=2, description="Medicine to request")
    quantity: int = Field(..., gt=0, description="Quantity to request for exchange")
    urgency: str = Field("Standard", description="'Standard' or 'Emergency'")
    request_notes: Optional[str] = Field(None, max_length=500, description="Optional notes or clinical reason")


class ExchangeStatusUpdate(BaseModel):
    status: str = Field(..., description="'Accepted', 'Rejected', 'Reserved', 'Dispatched', 'Completed', 'Cancelled'")
    response_notes: Optional[str] = Field(None, max_length=500, description="Optional response or dispatch remarks")


class ExchangeRequestResponse(BaseModel):
    id: str
    requesting_shop_id: str
    requesting_shop_name: Optional[str] = None
    requesting_phone: Optional[str] = None
    supplying_shop_id: str
    supplying_shop_name: Optional[str] = None
    supplying_phone: Optional[str] = None
    medicine_name: str
    quantity: int
    urgency: str
    status: str
    request_notes: Optional[str] = None
    response_notes: Optional[str] = None
    unit_price: float = 0.0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
