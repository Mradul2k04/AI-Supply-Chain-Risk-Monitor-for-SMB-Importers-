import uuid
import logging
from typing import List
from src.connectors.noaa import fetch_noaa_weather_signals
from src.connectors.usgs import fetch_usgs_earthquakes
from src.schemas.risk_event import RiskEvent

logger = logging.getLogger(__name__)

def run_weather_disaster_agent(
    supplier_id: str,
    country: str,
    city_or_region: str = None,
    lat: float = None,
    lon: float = None
) -> List[RiskEvent]:
    """
    Evaluates weather anomalies and earthquake hazards near supplier coordinates.
    """
    logger.info(f"Running Weather & Disaster Agent for supplier {supplier_id}")
    
    events = []
    
    # 1. Fetch weather warnings from NOAA
    weather_signals = fetch_noaa_weather_signals(country, city_or_region)
    for sig in weather_signals:
        events.append(
            RiskEvent(
                event_id=f"evt_noaa_{uuid.uuid4().hex[:8]}",
                risk_type="weather",
                title=sig.get("title", "Weather Warning"),
                severity=sig.get("severity", "medium"),
                event_date=sig.get("event_date"),
                region=city_or_region or country,
                source_url=sig.get("source_url", "https://noaa.gov"),
                source_name=sig.get("source_name", "NOAA Climate Office"),
                evidence_text=sig.get("evidence_text", ""),
                confidence=sig.get("confidence", 0.8)
            )
        )
        
    # 2. Fetch earthquake alerts from USGS
    if lat is not None and lon is not None:
        eq_signals = fetch_usgs_earthquakes(lat, lon, country)
        for sig in eq_signals:
            events.append(
                RiskEvent(
                    event_id=f"evt_usgs_{uuid.uuid4().hex[:8]}",
                    risk_type="earthquake",
                    title=sig.get("title", "Earthquake Signal"),
                    severity=sig.get("severity", "medium"),
                    event_date=sig.get("event_date"),
                    region=city_or_region or country,
                    source_url=sig.get("source_url", "https://earthquake.usgs.gov"),
                    source_name=sig.get("source_name", "USGS Hazards"),
                    evidence_text=sig.get("evidence_text", ""),
                    confidence=sig.get("confidence", 0.9)
                )
            )
            
    logger.info(f"Weather & Disaster Agent compiled {len(events)} events.")
    return events
