import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Sample internal history data for suppliers
INTERNAL_SUPPLIER_METRICS = {
    "SUP001": {
        "supplier_id": "SUP001",
        "name": "Chaozhou Ceramics Group",
        "historical_delay_rate": 0.05,
        "past_delays_count": 2,
        "defect_rate": 0.012,
        "on_time_delivery_rate": 0.95,
        "dependency_percent": 60.0,
        "safety_stock_weeks": 4.0,
        "annual_purchase_volume": 250000.0,
        "lead_time_days": 45
    },
    "SUP002": {
        "supplier_id": "SUP002",
        "name": "Global Microcircuits Ltd",
        "historical_delay_rate": 0.18,
        "past_delays_count": 6,
        "defect_rate": 0.035,
        "on_time_delivery_rate": 0.82,
        "dependency_percent": 80.0,
        "safety_stock_weeks": 6.0,
        "annual_purchase_volume": 450000.0,
        "lead_time_days": 60
    },
    "SUP003": {
        "supplier_id": "SUP003",
        "name": "Vietnam Plastics Jsc",
        "historical_delay_rate": 0.08,
        "past_delays_count": 3,
        "defect_rate": 0.02,
        "on_time_delivery_rate": 0.92,
        "dependency_percent": 30.0,
        "safety_stock_weeks": 3.0,
        "annual_purchase_volume": 120000.0,
        "lead_time_days": 30
    }
}

def fetch_internal_supplier_metrics(supplier_id: str) -> Dict[str, Any]:
    """
    Retrieve internal performance and order history metrics for a supplier.
    """
    logger.info(f"Retrieving internal metrics for supplier ID: {supplier_id}")
    metrics = INTERNAL_SUPPLIER_METRICS.get(supplier_id)
    if not metrics:
        # Return generic default metrics if not found
        return {
            "supplier_id": supplier_id,
            "name": "Unknown Supplier",
            "historical_delay_rate": 0.10,
            "past_delays_count": 0,
            "defect_rate": 0.02,
            "on_time_delivery_rate": 0.90,
            "dependency_percent": 20.0,
            "safety_stock_weeks": 3.0,
            "annual_purchase_volume": 50000.0,
            "lead_time_days": 30
        }
    return metrics

def get_all_internal_suppliers() -> List[Dict[str, Any]]:
    """Return all default mock supplier records."""
    return list(INTERNAL_SUPPLIER_METRICS.values())
