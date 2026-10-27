"""
Service module for handling medicine demand forecasting logic.
Will interface with serialized ML pipelines when trained.
"""

from typing import Any, Dict, List, Optional


class ForecastService:
    """Service to manage demand forecasting inference and model loading."""

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None

    def get_forecast(self, medicine_id: str, days_ahead: int) -> Dict[str, Any]:
        """
        Generate future demand forecast for a specified medicine.
        Note: ML model implementation pending.
        """
        raise NotImplementedError("Forecasting model is not yet trained or integrated.")

    def get_batch_forecast(self, medicine_ids: List[str], days_ahead: int) -> List[Dict[str, Any]]:
        """
        Generate future demand forecast for a list of medicines.
        Note: ML model implementation pending.
        """
        raise NotImplementedError("Batch forecasting model is not yet trained or integrated.")
