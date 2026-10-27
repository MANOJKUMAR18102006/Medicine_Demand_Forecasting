"""
Pydantic Schemas for Shop-Specific Medicines and Inventory Records.
"""

from typing import Optional
from pydantic import BaseModel, Field


class MedicineCreateRequest(BaseModel):
    medicine_name: str = Field(..., min_length=2, max_length=120, description="Name of the medicine")
    category: str = Field(..., min_length=2, max_length=80, description="Therapeutic category")
    unit_of_measurement: str = Field("units", max_length=40, description="e.g. tablets, strips, vials, bottles")
    unit_price: float = Field(10.0, ge=0.0, description="Unit sales price in currency")
    initial_stock: int = Field(100, ge=0, description="Starting inventory units on hand")
    safety_stock: Optional[int] = Field(20, ge=0, description="Safety stock buffer")
    reorder_threshold: Optional[int] = Field(50, ge=0, description="Minimum reorder threshold")


class MedicineItemResponse(BaseModel):
    id: str
    shop_id: str
    medicine_name: str
    category: str
    unit_of_measurement: str
    unit_price: float
    current_stock: int
    safety_stock: int
    reorder_threshold: int
    expiry_date: Optional[str] = None
    created_at: Optional[str] = None


class InventoryUpdateRequest(BaseModel):
    current_stock: int = Field(..., ge=0, description="Updated current physical stock units")
    safety_stock: Optional[int] = Field(None, ge=0, description="Updated safety stock buffer")
    reorder_threshold: Optional[int] = Field(None, ge=0, description="Updated reorder point")
    expiry_date: Optional[str] = Field(None, description="Optional batch expiration date")


class SeedStarterCatalogResponse(BaseModel):
    message: str
    medicines_added: int
