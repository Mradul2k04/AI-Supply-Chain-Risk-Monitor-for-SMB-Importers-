import uuid
import logging
from typing import List
from src.connectors.sec_edgar import fetch_sec_financial_signals
from src.schemas.risk_event import RiskEvent

logger = logging.getLogger(__name__)

def run_financial_signal_agent(supplier_name: str) -> List[RiskEvent]:
    """
    Reviews SEC EDGAR filings and licensed financial health metrics.
    """
    logger.info(f"Running Financial Signal Agent for supplier: {supplier_name}")
    
    events = []
    signals = fetch_sec_financial_signals(supplier_name)
    
    for sig in signals:
        events.append(
            RiskEvent(
                event_id=f"evt_sec_{uuid.uuid4().hex[:8]}",
                risk_type="financial",
                title=sig.get("title", "Financial Health Alert"),
                severity=sig.get("severity", "medium"),
                event_date=sig.get("event_date"),
                region="Global Financial",
                source_url=sig.get("source_url", "https://sec.gov"),
                source_name=sig.get("source_name", "SEC EDGAR"),
                evidence_text=sig.get("evidence_text", ""),
                confidence=sig.get("confidence", 0.85)
            )
        )
        
    logger.info(f"Financial Signal Agent compiled {len(events)} events.")
    return events
