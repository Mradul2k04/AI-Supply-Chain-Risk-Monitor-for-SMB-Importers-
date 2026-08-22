import logging
from typing import List
from src.schemas.supplier import Supplier
from src.schemas.risk_event import RiskEvent
from src.schemas.assessment import SupplierRiskAssessment
from src.services.scoring_service import calculate_supplier_risk

logger = logging.getLogger(__name__)

def run_risk_scoring_agent(supplier: Supplier, events: List[RiskEvent]) -> SupplierRiskAssessment:
    """
    Combines geopolitical, weather, and financial events into a structured assessment.
    """
    logger.info(f"Running Risk Scoring Agent for supplier ID: {supplier.supplier_id}")
    assessment = calculate_supplier_risk(
        supplier_id=supplier.supplier_id,
        events=events,
        product_categories=supplier.product_categories
    )
    logger.info(f"Risk evaluation complete. Score: {assessment.overall_risk_score}, Level: {assessment.risk_level}")
    return assessment
