"""
Prediction Service integrating with ML inference module.
"""

from typing import Dict, Any, List
from ml.predict import forecast_demand, get_forecaster


class PredictionService:
    """Service to handle medicine demand forecasts and catalog."""

    @staticmethod
    def get_available_medicines() -> List[str]:
        """Return list of all recognizable medicines in alphabetical order."""
        forecaster = get_forecaster()
        return sorted(forecaster.available_medicines)

    @staticmethod
    def predict_demand(medicine: str, days: int = 7) -> Dict[str, Any]:
        """Generate multi-step recursive demand forecast for medicine."""
        return forecast_demand(medicine, days)
