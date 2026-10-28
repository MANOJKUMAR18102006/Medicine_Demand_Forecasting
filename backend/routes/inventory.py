"""
Routes for inventory decision-support, medicine catalog, and multi-shop inventory management.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas.inventory import (
    InventoryAnalysisRequest,
    InventoryAnalysisResponse,
)
from backend.schemas.medicine import (
    MedicineCreateRequest,
    MedicineItemResponse,
    InventoryUpdateRequest,
    SeedStarterCatalogResponse,
)
from backend.services.inventory_service import InventoryService
from backend.services.prediction_service import PredictionService
from backend.services.shop_inventory_service import ShopInventoryService
from backend.services.auth_service import get_current_shop, get_optional_current_shop

router = APIRouter(prefix="", tags=["Inventory & Procurement"])


@router.get("/medicines", response_model=List[str])
def get_medicines_catalog(current_shop: Optional[Dict[str, Any]] = Depends(get_optional_current_shop)):
    """
    Return all available pharmaceutical drugs in the forecasting system.
    If authenticated as a medical shop, returns only medicines belonging to the shop.
    If unauthenticated, returns the shared base catalog.
    """
    try:
        if current_shop:
            shop_meds = ShopInventoryService.get_shop_medicine_names(current_shop["id"])
            return shop_meds
        return PredictionService.get_available_medicines()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to retrieve medicine catalog: {str(e)}",
        )


@router.get("/medicines/items", response_model=List[MedicineItemResponse])
def get_shop_medicine_items(current_shop: Dict[str, Any] = Depends(get_current_shop)):
    """
    Return full medicine and inventory records strictly belonging to the authenticated shop.
    """
    return ShopInventoryService.get_shop_medicines(current_shop["id"])


@router.post("/medicines", response_model=MedicineItemResponse, status_code=status.HTTP_201_CREATED)
def create_shop_medicine(
    payload: MedicineCreateRequest,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Add a new medicine and initial inventory to the authenticated medical shop's catalog.
    """
    return ShopInventoryService.add_medicine(
        shop_id=current_shop["id"],
        medicine_name=payload.medicine_name,
        category=payload.category,
        unit_of_measurement=payload.unit_of_measurement,
        unit_price=payload.unit_price,
        initial_stock=payload.initial_stock,
        safety_stock=payload.safety_stock or 20,
        reorder_threshold=payload.reorder_threshold or 50,
        dosage_form=payload.dosage_form or "Tablets",
        strength=payload.strength or "Standard",
        manufacturer=payload.manufacturer or "Generic Pharma",
        batch_number=payload.batch_number,
    )


@router.post("/medicines/seed-starter", response_model=SeedStarterCatalogResponse)
def seed_starter_medicines(current_shop: Dict[str, Any] = Depends(get_current_shop)):
    """
    Convenience endpoint for newly registered shops to seed standard pharmaceutical drugs.
    """
    count = ShopInventoryService.seed_starter_catalog(current_shop["id"])
    return {
        "message": f"Successfully loaded {count} starter medicines into your shop inventory.",
        "medicines_added": count,
    }


@router.post("/inventory/{medicine_identifier}", response_model=MedicineItemResponse)
def update_shop_inventory(
    medicine_identifier: str,
    payload: InventoryUpdateRequest,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Update stock levels and thresholds for a medicine in the authenticated medical shop.
    Medicine must belong to current_shop.
    """
    return ShopInventoryService.update_inventory_by_name_or_id(
        shop_id=current_shop["id"],
        medicine_identifier=medicine_identifier,
        current_stock=payload.current_stock,
        safety_stock=payload.safety_stock,
        reorder_threshold=payload.reorder_threshold,
        expiry_date=payload.expiry_date,
    )


@router.post("/inventory-analysis", response_model=InventoryAnalysisResponse)
def run_inventory_analysis(
    payload: InventoryAnalysisRequest,
    current_shop: Optional[Dict[str, Any]] = Depends(get_optional_current_shop),
):
    """
    Compute forecasted demand, safety stock, required stock, shortages,
    and recommended procurement order quantity.
    Enforces multi-tenant shop isolation when authenticated.
    """
    try:
        if current_shop:
            return ShopInventoryService.analyze_shop_inventory(
                shop_id=current_shop["id"],
                medicine_name=payload.medicine,
                days=payload.days,
                current_stock=payload.current_stock,
            )
        else:
            return InventoryService.analyze_medicine_inventory(
                medicine=payload.medicine,
                days=payload.days,
                current_stock=payload.current_stock,
            )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory calculation error: {str(e)}",
        )
