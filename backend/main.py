"""
FastAPI Application Entrypoint for Medicine Demand Forecasting & Inventory Optimization.
"""

import os
import sys
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routes.health import router as health_router
from backend.routes.auth import router as auth_router
from backend.routes.forecast import router as forecast_router
from backend.routes.inventory import router as inventory_router
from backend.routes.analytics import router as analytics_router
from ml.predict import get_forecaster


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database and pre-warm ML forecaster on startup."""
    print("Initiating FastAPI startup: initializing multi-shop database...")
    try:
        init_db()
        print("Multi-shop SQLite database verified and initialized.")
    except Exception as e:
        print(f"WARNING during DB init: {e}")

    print("Warming ML demand forecaster...")
    try:
        forecaster = get_forecaster()
        print(f"ML Model successfully loaded: {type(forecaster.model).__name__}")
        print(f"Recognized {len(forecaster.available_medicines)} pharmaceutical drugs.")
        from backend.routes.analytics import analytics_svc
        analytics_svc.get_dashboard_summary()
        print("Analytics dashboard summary pre-computed and cached.")
    except Exception as e:
        print(f"WARNING during startup: ML model pre-warm failed: {e}")
    yield
    print("FastAPI shutdown complete.")


app = FastAPI(
    title="Medicine Demand Forecasting & Inventory Optimization API",
    description="Enterprise Multi-Shop Machine Learning REST API for predictive healthcare supply chain management.",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for React Vite development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "MedDemand Multi-Shop Demand Forecasting and Inventory Optimization API is running.",
        "version": "2.0.0",
        "documentation": "/docs",
        "health_probe": "/api/health",
        "auth_routes": "/api/auth",
        "medicines_catalog": "/api/medicines",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
