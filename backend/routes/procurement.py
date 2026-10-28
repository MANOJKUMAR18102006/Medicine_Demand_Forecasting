"""
Routes for Authorized Supplier Medicine Marketplace & Purchase Orders.
Enforces multi-tenant authorization so shops only access their own procurement orders.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from backend.schemas.procurement import (
    SupplierResponse,
    SupplierProductResponse,
    PurchaseOrderCreateRequest,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
)
from backend.services.procurement_service import ProcurementService
from backend.services.auth_service import get_current_shop

router = APIRouter(prefix="/procurement", tags=["Supplier Marketplace & Procurement"])


@router.get("/suppliers", response_model=List[SupplierResponse])
def get_authorized_suppliers():
    """Return all authorized pharmaceutical suppliers and distributors."""
    return ProcurementService.list_suppliers()


@router.get("/products", response_model=List[SupplierProductResponse])
def search_marketplace_products(
    query: Optional[str] = Query(None, description="Search medicine, manufacturer, or dosage"),
    category: Optional[str] = Query(None, description="Filter therapeutic category"),
    supplier_id: Optional[str] = Query(None, description="Filter specific supplier"),
):
    """Search available medicine catalog across all verified suppliers."""
    return ProcurementService.search_products(
        query=query,
        category=category,
        supplier_id=supplier_id,
    )


@router.post("/orders", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    payload: PurchaseOrderCreateRequest,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Submit a purchase order for medicines to an authorized supplier.
    Verifies supplier available stock in real-time, decrements catalog inventory,
    and returns confirmed order details with tracking ID.
    """
    items_dicts = [i.model_dump() for i in payload.items]
    return ProcurementService.create_purchase_order(
        shop_id=current_shop["id"],
        supplier_id=payload.supplier_id,
        items=items_dicts,
        delivery_address=payload.delivery_address,
        payment_method=payload.payment_method,
        notes=payload.notes,
    )


@router.get("/orders", response_model=List[PurchaseOrderResponse])
def get_shop_purchase_orders(current_shop: Dict[str, Any] = Depends(get_current_shop)):
    """Retrieve purchase order history for the authenticated medical shop."""
    return ProcurementService.get_shop_purchase_orders(current_shop["id"])


@router.get("/orders/{order_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    order_id: str,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """Retrieve full line items and status tracking for a specific purchase order."""
    return ProcurementService.get_order_by_id(current_shop["id"], order_id)


@router.patch("/orders/{order_id}/status", response_model=PurchaseOrderResponse)
def update_purchase_order_status(
    order_id: str,
    payload: PurchaseOrderStatusUpdate,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Update purchase order status:
    - Confirmed / Processing / Dispatched
    - Delivered: Automatically transfers stock into shop's physical inventory
    - Cancelled: Restores supplier stock
    """
    return ProcurementService.update_order_status(
        shop_id=current_shop["id"],
        order_id=order_id,
        new_status=payload.status,
        notes=payload.notes,
    )
