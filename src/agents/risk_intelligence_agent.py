import uuid
import logging
from typing import List, Dict, Any
from src.connectors.gdelt import fetch_gdelt_risk_signals
from src.connectors.reliefweb import fetch_reliefweb_signals
from src.schemas.risk_event import RiskEvent

logger = logging.getLogger(__name__)

def run_risk_intelligence_agent(supplier_name: str, country: str, region: str = None, port: str = None) -> List[RiskEvent]:
    """
    Collects and normalizes news and geopolitical risk events.
    """
    logger.info(f"Running Risk Intelligence Agent for {supplier_name} ({country})")
    
    # 1. Fetch Geopolitical Signals from GDELT
    gdelt_signals = fetch_gdelt_risk_signals(country, region, port)
    
    # 2. Fetch Disaster Signals from ReliefWeb
    reliefweb_signals = fetch_reliefweb_signals(country, region)
    
    candidate_events = []
    
    # Process GDELT signals
    for sig in gdelt_signals:
        candidate_events.append(
            RiskEvent(
                event_id=f"evt_gdelt_{uuid.uuid4().hex[:8]}",
                risk_type=sig.get("risk_type", "geopolitical"),
                title=sig.get("title", "Geopolitical Alert"),
                severity=sig.get("severity", "medium"),
                event_date=sig.get("event_date"),
                region=region or country,
                source_url=sig.get("source_url", "https://gdeltproject.org"),
                source_name=sig.get("source_name", "GDELT"),
                evidence_text=sig.get("evidence_text", ""),
                confidence=sig.get("confidence", 0.7)
            )
        )
        
    # Process ReliefWeb signals
    for sig in reliefweb_signals:
        candidate_events.append(
            RiskEvent(
                event_id=f"evt_rw_{uuid.uuid4().hex[:8]}",
                risk_type="weather",
                title=sig.get("title", "Humanitarian Alert"),
                severity=sig.get("severity", "high"),
                event_date=sig.get("event_date"),
                region=region or country,
                source_url=sig.get("source_url", "https://reliefweb.int"),
                source_name=sig.get("source_name", "ReliefWeb"),
                evidence_text=sig.get("evidence_text", ""),
                confidence=sig.get("confidence", 0.8)
            )
        )
        
    logger.info(f"Compiled {len(candidate_events)} candidate risk events.")
    return candidate_events
