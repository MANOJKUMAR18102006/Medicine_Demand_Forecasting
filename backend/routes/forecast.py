"""
Routes for demand forecasting and multi-shop forecast history.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas.forecast import ForecastRequest, ForecastResponse
from backend.services.prediction_service import PredictionService
from backend.services.shop_inventory_service import ShopInventoryService
from backend.services.auth_service import get_optional_current_shop, get_current_shop

router = APIRouter(prefix="", tags=["Demand Forecasting"])


@router.post("/forecast", response_model=ForecastResponse)
def get_demand_forecast(
    payload: ForecastRequest,
    current_shop: Optional[Dict[str, Any]] = Depends(get_optional_current_shop),
):
    """
    Generate recursive multi-step demand forecast for a medicine using XGBoost.
    Supports 7, 14, and 30-day forecast horizons.
    Associates forecast history with authenticated medical shop.
    """
    try:
        result = PredictionService.predict_demand(
            medicine=payload.medicine,
            days=payload.days,
        )

        # Record forecast under current shop if authenticated
        if current_shop:
            ShopInventoryService.save_forecast_history(
                shop_id=current_shop["id"],
                medicine_name=payload.medicine,
                horizon=payload.days,
                predicted_demand=result["total_predicted_demand"],
                details=result.get("forecast", []),
            )

        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting error: {str(e)}",
        )


@router.get("/forecasts/history")
def get_forecast_history(
    limit: int = 15,
    current_shop: Dict[str, Any] = Depends(get_current_shop),
):
    """
    Retrieve forecast execution logs strictly belonging to the authenticated medical shop.
    """
    return ShopInventoryService.get_shop_forecast_history(current_shop["id"], limit=limit)
