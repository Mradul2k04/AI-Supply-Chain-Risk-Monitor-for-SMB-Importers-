import os
import logging
import requests
from typing import Dict, Any, List
from src.schemas.supplier import Supplier

logger = logging.getLogger(__name__)

# Standard geocode coordinates for major supplier cities/ports
DEFAULT_GEOCODES = {
    "shanghai": (31.23, 121.47),
    "shenzhen": (22.54, 114.05),
    "ho chi minh city": (10.82, 106.63),
    "hanoi": (21.02, 105.83),
    "manila": (14.59, 120.98),
    "rotterdam": (51.92, 4.47),
    "keelung": (25.12, 121.74),
    "panama city": (8.98, -79.51)
}

def geocode_location(city_or_region: str, country: str) -> tuple[float, float]:
    """
    Geocodes city and country using Nominatim API.
    Falls back to a dictionary of predefined major cities.
    """
    if not city_or_region:
        return 0.0, 0.0
        
    query = f"{city_or_region}, {country}"
    base_url = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org").rstrip('/')
    url = f"{base_url}/search?q={query}&format=json&limit=1"
    headers = {"User-Agent": "supply-chain-risk-monitor-smb"}
    
    try:
        logger.info(f"Querying OpenStreetMap Nominatim for: {query}")
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                logger.info(f"Geocoded successfully: ({lat}, {lon})")
                return lat, lon
    except Exception as e:
        logger.warning(f"OSM geocoding failed: {e}. Checking predefined map.")

    # Preset fallback checking
    key = city_or_region.lower().strip()
    if key in DEFAULT_GEOCODES:
        return DEFAULT_GEOCODES[key]
        
    # Check if country has default coordinates
    country_lower = country.lower().strip()
    if "china" in country_lower:
        return 31.23, 121.47
    elif "vietnam" in country_lower:
        return 10.82, 106.63
    elif "philippines" in country_lower:
        return 14.59, 120.98
    elif "netherlands" in country_lower:
        return 51.92, 4.47
    elif "panama" in country_lower:
        return 8.98, -79.51
        
    return 0.0, 0.0

def run_supplier_profile_agent(raw_data: Dict[str, Any]) -> Supplier:
    """
    Processes and normalizes supplier profile inputs.
    """
    supplier_id = raw_data.get("supplier_id", "SUP_UNKNOWN")
    name = raw_data.get("name", "Unnamed Vendor")
    country = raw_data.get("country", "Unknown")
    city_or_region = raw_data.get("city_or_region")
    primary_port = raw_data.get("primary_port")
    
    # Extract coordinates
    lat = raw_data.get("latitude")
    lon = raw_data.get("longitude")
    if lat is None or lon is None:
        lat, lon = geocode_location(city_or_region or primary_port, country)
        
    # Normalise lists
    categories = raw_data.get("product_categories", [])
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",") if c.strip()]
        
    alternates = raw_data.get("approved_alternate_supplier_ids", [])
    if isinstance(alternates, str):
        alternates = [a.strip() for a in alternates.split(",") if a.strip()]

    # Validate output structure
    supplier = Supplier(
        supplier_id=supplier_id,
        name=name,
        country=country,
        city_or_region=city_or_region,
        latitude=lat,
        longitude=lon,
        product_categories=categories,
        primary_port=primary_port,
        dependency_percent=raw_data.get("dependency_percent"),
        lead_time_days=raw_data.get("lead_time_days"),
        approved_alternate_supplier_ids=alternates
    )
    
    logger.info(f"Supplier profile normalized successfully: {supplier.supplier_id}")
    return supplier
