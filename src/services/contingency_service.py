import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from src.services.database import DBContingencyPlan
from src.schemas.contingency import ContingencyPlan

logger = logging.getLogger(__name__)

def get_contingency_plan(db: Session, supplier_id: str, trigger_event_id: str) -> Optional[ContingencyPlan]:
    db_plan = db.query(DBContingencyPlan).filter(
        DBContingencyPlan.supplier_id == supplier_id,
        DBContingencyPlan.trigger_event_id == trigger_event_id
    ).first()
    
    if not db_plan:
        return None
        
    return ContingencyPlan(
        supplier_id=db_plan.supplier_id,
        trigger_event_id=db_plan.trigger_event_id,
        recommended_action=db_plan.recommended_action,
        alternate_supplier_id=db_plan.alternate_supplier_id,
        proposed_volume_shift_percent=db_plan.proposed_volume_shift_percent,
        estimated_lead_time_delta_days=db_plan.estimated_lead_time_delta_days,
        assumptions=db_plan.assumptions,
        evidence_links=db_plan.evidence_links,
        approval_status=db_plan.approval_status
    )

def list_contingency_plans(db: Session) -> List[ContingencyPlan]:
    db_plans = db.query(DBContingencyPlan).all()
    return [
        ContingencyPlan(
            supplier_id=p.supplier_id,
            trigger_event_id=p.trigger_event_id,
            recommended_action=p.recommended_action,
            alternate_supplier_id=p.alternate_supplier_id,
            proposed_volume_shift_percent=p.proposed_volume_shift_percent,
            estimated_lead_time_delta_days=p.estimated_lead_time_delta_days,
            assumptions=p.assumptions,
            evidence_links=p.evidence_links,
            approval_status=p.approval_status
        ) for p in db_plans
    ]

def save_contingency_plan(db: Session, plan: ContingencyPlan) -> ContingencyPlan:
    logger.info(f"Saving contingency plan for supplier {plan.supplier_id} triggered by {plan.trigger_event_id}")
    db_plan = db.query(DBContingencyPlan).filter(
        DBContingencyPlan.supplier_id == plan.supplier_id,
        DBContingencyPlan.trigger_event_id == plan.trigger_event_id
    ).first()
    
    if db_plan:
        db_plan.recommended_action = plan.recommended_action
        db_plan.alternate_supplier_id = plan.alternate_supplier_id
        db_plan.proposed_volume_shift_percent = plan.proposed_volume_shift_percent
        db_plan.estimated_lead_time_delta_days = plan.estimated_lead_time_delta_days
        db_plan.assumptions = plan.assumptions
        db_plan.evidence_links = plan.evidence_links
        db_plan.approval_status = plan.approval_status
    else:
        db_plan = DBContingencyPlan(
            supplier_id=plan.supplier_id,
            trigger_event_id=plan.trigger_event_id,
            recommended_action=plan.recommended_action,
            alternate_supplier_id=plan.alternate_supplier_id,
            proposed_volume_shift_percent=plan.proposed_volume_shift_percent,
            estimated_lead_time_delta_days=plan.estimated_lead_time_delta_days,
            assumptions=plan.assumptions,
            evidence_links=plan.evidence_links,
            approval_status=plan.approval_status
        )
        db.add(db_plan)
        
    db.commit()
    return plan

def update_plan_status(db: Session, supplier_id: str, trigger_event_id: str, status: str) -> bool:
    db_plan = db.query(DBContingencyPlan).filter(
        DBContingencyPlan.supplier_id == supplier_id,
        DBContingencyPlan.trigger_event_id == trigger_event_id
    ).first()
    
    if db_plan:
        db_plan.approval_status = status
        db.commit()
        logger.info(f"Updated plan status for supplier {supplier_id} to {status}")
        return True
    return False
