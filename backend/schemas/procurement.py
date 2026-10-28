"""
Pydantic Schemas for Authorized Supplier Marketplace and Purchase Orders.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SupplierResponse(BaseModel):
    id: str
    supplier_name: str
    contact_person: Optional[str] = None
    email: str
    phone_number: str
    address: str
    license_number: str
    rating: float = 4.8
    is_verified: int = 1


class SupplierProductResponse(BaseModel):
    id: str
    supplier_id: str
    supplier_name: Optional[str] = None
    supplier_rating: Optional[float] = None
    medicine_name: str
    category: str
    dosage_form: str = "Tablets"
    strength: str = "Standard"
    manufacturer: str = "Authorized Pharma"
    unit_price: float
    available_quantity: int
    unit_of_measurement: str = "units"
    batch_number: str
    expiry_date: str
    estimated_delivery_days: int = 2
    min_order_quantity: int = 10
    is_active: int = 1


class PurchaseOrderItemCreate(BaseModel):
    supplier_product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)


class PurchaseOrderCreateRequest(BaseModel):
    supplier_id: str = Field(..., min_length=1)
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1)
    delivery_address: str = Field(..., min_length=5)
    payment_method: str = Field("Net 30 Invoice", description="Net 30 Invoice, Cash on Delivery, Bank Transfer")
    notes: Optional[str] = Field(None, max_length=500)


class PurchaseOrderItemResponse(BaseModel):
    id: str
    supplier_product_id: str
    medicine_name: str
    category: Optional[str] = None
    dosage_form: Optional[str] = None
    strength: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float


class PurchaseOrderResponse(BaseModel):
    id: str
    shop_id: str
    shop_name: Optional[str] = None
    supplier_id: str
    supplier_name: Optional[str] = None
    status: str
    total_amount: float
    payment_method: str
    payment_status: str
    delivery_address: str
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    inventory_applied: int = 0
    items: List[PurchaseOrderItemResponse] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PurchaseOrderStatusUpdate(BaseModel):
    status: str = Field(..., description="Pending, Confirmed, Processing, Dispatched, Delivered, Cancelled")
    notes: Optional[str] = Field(None, max_length=500)
