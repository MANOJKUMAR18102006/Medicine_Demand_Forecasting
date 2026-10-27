"""
Inventory Service integrating with ML inventory optimizer.
"""

from typing import Dict, Any, Optional
from ml.inventory_optimizer import analyze_inventory


class InventoryService:
    """Service to execute inventory decision-support and procurement optimization."""

    @staticmethod
    def analyze_medicine_inventory(
        medicine: str,
        days: int = 7,
        current_stock: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform comprehensive inventory analysis and generate recommendations."""
        return analyze_inventory(medicine, days, current_stock)
