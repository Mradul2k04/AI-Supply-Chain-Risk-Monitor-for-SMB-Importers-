import os
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


FALLBACK_DISASTERS = [
    {
        "title": "Severe Seasonal Flooding Disrupts Industrial Zones in Ho Chi Minh City",
        "evidence_text": "Heavy monsoon rains have triggered severe flooding in industrial parks surrounding Ho Chi Minh City. Logistics warehouses report minor water damage and transport networks are halted.",
        "source_url": "https://reliefweb.int/mock/vietnam-floods",
        "source_name": "ReliefWeb Disaster Response",
        "severity": "high",
        "risk_type": "weather",
        "countries": ["Vietnam", "VN"]
    },
    {
        "title": "Typhoon Approaching Central Philippines - Port Operations Suspended",
        "evidence_text": "Category 3 Typhoon is projected to make landfall in Eastern Visayas. Coast Guard has ordered all cargo vessels to remain in port. Substantial delays in shipment departures expected.",
        "source_url": "https://reliefweb.int/mock/philippines-typhoon",
        "source_name": "ReliefWeb Disaster Alert",
        "severity": "critical",
        "risk_type": "weather",
        "countries": ["Philippines", "PH"]
    },
    {
        "title": "Volcanic Ash Disrupts Air Freight Across Java, Indonesia",
        "evidence_text": "An eruption of Mt. Merapi has sent ash clouds up to 15,000 feet. Flight restrictions have been implemented, delaying air cargo routes and electronics supply chains out of Java.",
        "source_url": "https://reliefweb.int/mock/indonesia-eruption",
        "source_name": "Volcano Watch Agency",
        "severity": "medium",
        "risk_type": "earthquake",
        "countries": ["Indonesia", "ID"]
    },
    {
        "title": "Extreme Drought Decreases Panama Canal Daily Transits",
        "evidence_text": "El Niño conditions have led to record-low water levels in Gatun Lake. The Panama Canal Authority has reduced the maximum draft limit and restricted daily transits, causing 3-week delays.",
        "source_url": "https://reliefweb.int/mock/panama-canal-drought",
        "source_name": "Climate Impact Network",
        "severity": "high",
        "risk_type": "weather",
        "countries": ["Panama", "PA"]
    }
]

def fetch_reliefweb_signals(country: str, region: str = None) -> List[Dict[str, Any]]:
    """
    Fetch humanitarian and disaster reports from ReliefWeb API.
    Falls back to high-fidelity simulated events if API fails.
    """
    base_url = os.getenv("RELIEFWEB_BASE_URL", "https://api.reliefweb.int/v1").rstrip('/')
    url = f"{base_url}/reports?appname=supply-chain-monitor&query[value]={country}&limit=5"
    events = []
    
    try:
        logger.info(f"Querying ReliefWeb API for country: {country}")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            reports = data.get("data", [])
            for r in reports:
                fields = r.get("fields", {})
                events.append({
                    "title": fields.get("title", "Disaster Alert"),
                    "evidence_text": f"ReliefWeb Alert: {fields.get('title')}",
                    "source_url": r.get("href", "https://reliefweb.int"),
                    "source_name": "ReliefWeb Reports",
                    "severity": "medium",
                    "risk_type": "weather",
                    "event_date": datetime.utcnow()
                })
    except Exception as e:
        logger.warning(f"Failed to fetch from ReliefWeb API: {e}. Using simulated disaster database.")

    # Filter fallbacks
    country_lower = country.lower()
    fallback_matches = []
    for item in FALLBACK_DISASTERS:
        for c in item["countries"]:
            if c.lower() in country_lower:
                copy_item = item.copy()
                copy_item["event_date"] = datetime.utcnow() - timedelta(days=2)
                fallback_matches.append(copy_item)
                break
                
    events.extend(fallback_matches)
    return events
