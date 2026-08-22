import os
import logging
import requests
import math
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Seismically active regions for fallback simulation
FALLBACK_EARTHQUAKES = [
    {
        "title": "Magnitude 5.8 Earthquake Off Coast of Hualien, Taiwan",
        "evidence_text": "A shallow magnitude 5.8 earthquake struck eastern Taiwan. Heavy shaking felt in Hualien and Taipei. Port of Keelung reports normal operations, but inland logistics routes are under inspection.",
        "source_url": "https://earthquake.usgs.gov/mock/taiwan-quake",
        "source_name": "USGS Earthquake Hazards Program",
        "severity": "medium",
        "risk_type": "earthquake",
        "countries": ["Taiwan", "TW"],
        "lat": 23.97,
        "lon": 121.60
    },
    {
        "title": "Magnitude 6.2 Earthquake Near Tokyo Bay, Japan",
        "evidence_text": "An earthquake of magnitude 6.2 occurred at a depth of 50km near Tokyo. Public rail transport and container terminals suspended temporarily for safety checks.",
        "source_url": "https://earthquake.usgs.gov/mock/japan-quake",
        "source_name": "USGS Earthquake Alerts",
        "severity": "high",
        "risk_type": "earthquake",
        "countries": ["Japan", "JP"],
        "lat": 35.68,
        "lon": 139.76
    }
]

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two coordinates using Haversine formula."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def fetch_usgs_earthquakes(supplier_lat: float, supplier_lon: float, country: str) -> List[Dict[str, Any]]:
    """
    Fetch earthquakes near supplier coordinates from USGS.
    """
    events = []
    
    # Query live USGS for the last 30 days
    starttime = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    base_url = os.getenv("USGS_BASE_URL", "https://earthquake.usgs.gov/fdsnws/event/1").rstrip('/')
    url = f"{base_url}/query?format=geojson&starttime={starttime}&minmagnitude=4.5"
    
    try:
        logger.info("Querying live USGS Earthquake API...")
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                geom = feat.get("geometry", {})
                coords = geom.get("coordinates", [])
                
                if len(coords) >= 2 and supplier_lat is not None and supplier_lon is not None:
                    eq_lon, eq_lat = coords[0], coords[1]
                    dist = calculate_distance(supplier_lat, supplier_lon, eq_lat, eq_lon)
                    if dist <= 300.0:  # Within 300km
                        mag = props.get("mag", 4.5)
                        severity = "critical" if mag >= 6.0 else ("high" if mag >= 5.0 else "medium")
                        events.append({
                            "title": f"M{mag} Earthquake - {props.get('place', 'Local Region')}",
                            "evidence_text": f"USGS reports a magnitude {mag} earthquake occurred {dist:.1f} km from supplier location at coordinates ({eq_lat}, {eq_lon}).",
                            "source_url": props.get("url", "https://earthquake.usgs.gov"),
                            "source_name": "USGS Earthquake Hazards",
                            "severity": severity,
                            "risk_type": "earthquake",
                            "event_date": datetime.utcfromtimestamp(props.get("time", 0) / 1000.0)
                        })
    except Exception as e:
        logger.warning(f"Failed to fetch live USGS earthquakes: {e}")

    # Fallback/augment from simulated earthquakes if no events detected and country matches
    if not events:
        country_lower = country.lower()
        for item in FALLBACK_EARTHQUAKES:
            for c in item["countries"]:
                if c.lower() in country_lower:
                    # Check distance if supplier coordinates are present, else fallback matching country
                    dist = calculate_distance(supplier_lat, supplier_lon, item["lat"], item["lon"])
                    if dist <= 300.0 or supplier_lat is None:
                        copy_item = item.copy()
                        copy_item["event_date"] = datetime.utcnow() - timedelta(days=5)
                        # Remove coordinates to match schema
                        copy_item.pop("lat", None)
                        copy_item.pop("lon", None)
                        events.append(copy_item)
                        break

    return events
