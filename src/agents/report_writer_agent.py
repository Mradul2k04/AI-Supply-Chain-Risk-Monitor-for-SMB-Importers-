import logging
from typing import Dict, Any, List
from datetime import datetime
from src.schemas.supplier import Supplier
from src.schemas.assessment import SupplierRiskAssessment
from src.schemas.contingency import ContingencyPlan

logger = logging.getLogger(__name__)

def run_report_writer_agent(
    supplier: Supplier,
    assessment: SupplierRiskAssessment,
    approved_plans: List[ContingencyPlan]
) -> Dict[str, Any]:
    """
    Compiles supplier profiles, risk scores, and approved mitigation options.
    """
    logger.info(f"Running Report Writer Agent for supplier: {supplier.name}")
    
    plans_summary = []
    for plan in approved_plans:
        plans_summary.append({
            "trigger_event_id": plan.trigger_event_id,
            "recommended_action": plan.recommended_action,
            "alternate_supplier_id": plan.alternate_supplier_id or "None",
            "volume_shift_percent": plan.proposed_volume_shift_percent or 0.0,
            "lead_time_impact_days": plan.estimated_lead_time_delta_days or 0,
            "approval_status": plan.approval_status
        })
        
    report = {
        "report_id": f"REP_{supplier.supplier_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "supplier_id": supplier.supplier_id,
        "supplier_name": supplier.name,
        "location": f"{supplier.city_or_region or 'N/A'}, {supplier.country}",
        "primary_port": supplier.primary_port or "None",
        "dependency_exposure": f"{supplier.dependency_percent or 0.0}%",
        "overall_risk_score": assessment.overall_risk_score,
        "risk_level": assessment.risk_level.upper(),
        "operational_impact": assessment.operational_impact,
        "confidence_level": f"{int(assessment.confidence * 100)}%",
        "approved_mitigation_actions": plans_summary
    }
    
    logger.info(f"Compiled risk report for {supplier.name} successfully.")
    return report
