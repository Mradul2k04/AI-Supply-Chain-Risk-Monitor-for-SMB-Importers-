from typing import List, Dict, Any, Optional, TypedDict
from src.schemas.supplier import Supplier
from src.schemas.risk_event import RiskEvent
from src.schemas.assessment import SupplierRiskAssessment
from src.schemas.contingency import ContingencyPlan

class RiskMonitorState(TypedDict):
    # Core Data
    supplier_input: Dict[str, Any]
    supplier: Optional[Supplier]
    
    # Risk Collection findings
    geopolitical_events: List[RiskEvent]
    weather_events: List[RiskEvent]
    financial_events: List[RiskEvent]
    all_events: List[RiskEvent]
    
    # Evaluated risk
    risk_assessment: Optional[SupplierRiskAssessment]
    
    # Contingency & Reporting
    contingency_plans: List[ContingencyPlan]
    compiled_report: Optional[Dict[str, Any]]
    
    # Human Gate Checkpoint approvals
    review_status: str  # "pending", "approved", "rejected", "rework"
    review_feedback: Optional[str]
