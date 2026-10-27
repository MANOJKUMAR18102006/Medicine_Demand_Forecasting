"""
Routes for analytics dashboard and model evaluation metrics.
Provides tenant-isolated analytics for authenticated medical shops.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from backend.schemas.analytics import AnalyticsSummaryResponse, ModelMetricsResponse
from backend.services.analytics_service import AnalyticsService
from backend.services.shop_inventory_service import ShopInventoryService
from backend.services.auth_service import get_optional_current_shop

router = APIRouter(prefix="", tags=["Analytics & Evaluation"])
analytics_svc = AnalyticsService()


@router.get("/model-metrics", response_model=ModelMetricsResponse)
def get_model_evaluation_metrics():
    """
    Return model performance comparison table (Linear Regression, Random Forest, XGBoost)
    with genuine holdout Test MAE, RMSE, R2, and Safe MAPE. Shared across all shops.
    """
    try:
        return analytics_svc.get_model_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read model metrics: {str(e)}",
        )


@router.get("/analytics/summary")
def get_dashboard_analytics(
    current_shop: Optional[Dict[str, Any]] = Depends(get_optional_current_shop),
):
    """
    Return operational statistics, stock alerts, monthly trends, and medicine demand summaries.
    Enforces strict multi-shop tenant isolation when authenticated: only the authenticated
    shop's medicines and inventory levels are aggregated.
    """
    try:
        if current_shop:
            return ShopInventoryService.get_shop_dashboard_summary(current_shop["id"])
        return analytics_svc.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to compute dashboard analytics: {str(e)}",
        )
