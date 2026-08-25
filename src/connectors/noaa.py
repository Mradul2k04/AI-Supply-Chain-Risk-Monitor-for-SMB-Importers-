import os
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

NOAA_TOKEN = os.getenv("NOAA_TOKEN", "")

FALLBACK_WEATHER = [
    {
        "title": "Severe Heatwave Triggers Power Rationing in East Asian Ports",
        "evidence_text": "An unprecedented summer heatwave has forced regional grids to implement load-shedding. Factories and port terminals face scheduled power cuts, slowing cargo staging.",
        "source_url": "https://www.noaa.gov/mock/east-asia-heatwave",
        "source_name": "NOAA Climate Observations",
        "severity": "medium",
        "risk_type": "weather",
        "countries": ["China", "Taiwan", "Japan"]
    },
    {
        "title": "Heavy Winter Freeze Impacts Northern Logistics Corridors",
        "evidence_text": "Sub-zero temperatures and heavy snowstorms have frozen waterways and blocked freight rail lines in northern corridors, causing transit delays of 3 to 5 days.",
        "source_url": "https://www.noaa.gov/mock/northern-winter-freeze",
        "source_name": "National Weather Service",
        "severity": "medium",
        "risk_type": "weather",
        "countries": ["Canada", "United States", "US", "Germany", "Poland"]
    },
    {
        "title": "Monsoon Season Delay Causes Dry Spells and Low Water Levels",
        "evidence_text": "A delayed southwest monsoon has led to historically low river levels, restricting barge cargo weight capacity on major shipping rivers.",
        "source_url": "https://www.noaa.gov/mock/river-drought",
        "source_name": "Global Hydrology Monitor",
        "severity": "medium",
        "risk_type": "weather",
        "countries": ["India", "Vietnam", "Thailand"]
    }
]

def fetch_noaa_weather_signals(country: str, city_or_region: str = None) -> List[Dict[str, Any]]:
    """
    Fetch NOAA weather anomaly signals from NOAA_BASE_URL or local fallbacks.
    """
    events = []
    noaa_base_url = os.getenv("NOAA_BASE_URL", "").strip()
    
    if noaa_base_url:
        try:
            logger.info(f"Querying NOAA active weather alerts at: {noaa_base_url}")
            # weather.gov API requires a User-Agent header
            headers = {"User-Agent": "supply-chain-risk-monitor-smb"}
            response = requests.get(noaa_base_url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                features = data.get("features", [])
                for f in features:
                    props = f.get("properties", {})
                    raw_sev = str(props.get("severity", "medium")).lower()
                    if raw_sev in ["minor", "low"]:
                        severity = "low"
                    elif raw_sev in ["moderate", "medium"]:
                        severity = "medium"
                    elif raw_sev in ["severe", "high"]:
                        severity = "high"
                    elif raw_sev in ["extreme", "critical"]:
                        severity = "critical"
                    else:
                        severity = "medium"

                    headline = props.get("headline") or ""
                    description = props.get("description") or ""
                    evidence_text = f"{headline}\n{description}".strip() if (headline or description) else "Active NOAA Weather Alert reported."

                    events.append({
                        "title": props.get("event") or "Active Weather Alert",
                        "evidence_text": evidence_text,
                        "source_url": props.get("@id") or "https://api.weather.gov",
                        "source_name": "NOAA Weather Alerts",
                        "severity": severity,
                        "risk_type": "weather",
                        "event_date": datetime.utcnow()
                    })
                    if len(events) >= 3:
                        break
        except Exception as e:
            logger.warning(f"NOAA Weather API query failed: {e}")

    if not events and NOAA_TOKEN:
        try:
            logger.info("Querying NOAA Climate Data Online API fallback")
            headers = {"token": NOAA_TOKEN}
            url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data?datasetid=GHCND&limit=5"
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Parse CDO response if needed
                pass
        except Exception as e:
            logger.warning(f"NOAA CDO API query failed: {e}")

    # Fallback simulation
    country_lower = country.lower()
    fallback_matches = []
    for item in FALLBACK_WEATHER:
        for c in item["countries"]:
            if c.lower() in country_lower:
                copy_item = item.copy()
                copy_item["event_date"] = datetime.utcnow() - timedelta(days=3)
                fallback_matches.append(copy_item)
                break
                
    events.extend(fallback_matches)
    
    # If no seasonal weather records found, return a default low weather risk event
    if not events:
        events.append({
            "title": f"Normal Seasonal Weather Conditions in {country}",
            "evidence_text": f"Weather forecasting models indicate normal temperature and wind parameters for supplier operations in {country}.",
            "source_url": "https://www.noaa.gov/mock/weather-status",
            "source_name": "NWS Climate Prediction Center",
            "severity": "low",
            "risk_type": "weather",
            "event_date": datetime.utcnow()
        })
        
    return events
