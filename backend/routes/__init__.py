from .health import router as health_router
from .forecast import router as forecast_router
from .inventory import router as inventory_router
from .analytics import router as analytics_router

__all__ = ["health_router", "forecast_router", "inventory_router", "analytics_router"]
