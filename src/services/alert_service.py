import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from src.services.database import DBRiskEvent
from src.schemas.risk_event import RiskEvent

logger = logging.getLogger(__name__)

def get_risk_event_by_id(db: Session, event_id: str) -> Optional[RiskEvent]:
    db_event = db.query(DBRiskEvent).filter(DBRiskEvent.event_id == event_id).first()
    if not db_event:
        return None
    return RiskEvent(
        event_id=db_event.event_id,
        risk_type=db_event.risk_type,
        title=db_event.title,
        severity=db_event.severity,
        event_date=db_event.event_date,
        region=db_event.region,
        source_url=db_event.source_url,
        source_name=db_event.source_name,
        evidence_text=db_event.evidence_text,
        confidence=db_event.confidence
    )

def list_active_risk_events(db: Session) -> List[RiskEvent]:
    db_events = db.query(DBRiskEvent).all()
    return [
        RiskEvent(
            event_id=e.event_id,
            risk_type=e.risk_type,
            title=e.title,
            severity=e.severity,
            event_date=e.event_date,
            region=e.region,
            source_url=e.source_url,
            source_name=e.source_name,
            evidence_text=e.evidence_text,
            confidence=e.confidence
        ) for e in db_events
    ]

def save_risk_event(db: Session, event: RiskEvent) -> RiskEvent:
    logger.info(f"Saving risk event: {event.event_id} - {event.title}")
    db_event = db.query(DBRiskEvent).filter(DBRiskEvent.event_id == event.event_id).first()
    
    if db_event:
        db_event.risk_type = event.risk_type
        db_event.title = event.title
        db_event.severity = event.severity
        db_event.event_date = event.event_date
        db_event.region = event.region
        db_event.source_url = event.source_url
        db_event.source_name = event.source_name
        db_event.evidence_text = event.evidence_text
        db_event.confidence = event.confidence
    else:
        db_event = DBRiskEvent(
            event_id=event.event_id,
            risk_type=event.risk_type,
            title=event.title,
            severity=event.severity,
            event_date=event.event_date,
            region=event.region,
            source_url=event.source_url,
            source_name=event.source_name,
            evidence_text=event.evidence_text,
            confidence=event.confidence
        )
        db.add(db_event)
        
    db.commit()
    return event

def delete_risk_event(db: Session, event_id: str) -> bool:
    db_event = db.query(DBRiskEvent).filter(DBRiskEvent.event_id == event_id).first()
    if db_event:
        db.delete(db_event)
        db.commit()
        logger.info(f"Deleted risk event ID: {event_id}")
        return True
    return False
