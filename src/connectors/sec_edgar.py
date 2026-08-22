import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Sample public company or mock financial risks for suppliers
FALLBACK_FINANCIAL_REPORTS = [
    {
        "title": "Restructuring of Long-Term Debt and Liquidity Warning",
        "evidence_text": "Public regulatory filing reports that the supplier's parent entity has initiated a debt restructuring program after a 25% year-over-year revenue decline. Operating cash flows are flagged as insufficient for the next 12 months.",
        "source_url": "https://www.sec.gov/edgar/mock/restructuring-filing",
        "source_name": "SEC EDGAR Filing Form 10-Q",
        "severity": "high",
        "risk_type": "financial",
        "supplier_names": ["Chaozhou Ceramics Group", "Global Microcircuits Ltd", "Pacific Electronics Corp"]
    },
    {
        "title": "Credit Rating Downgraded to Sub-Investment Grade",
        "evidence_text": "International credit rating agency downgraded the supplier's credit rank to BB- due to elevated leverage ratios and supply chain cost inflation. Supplier's financing capacity is expected to contract.",
        "source_url": "https://www.sec.gov/edgar/mock/credit-downgrade",
        "source_name": "Credit Intelligence Reports",
        "severity": "medium",
        "risk_type": "financial",
        "supplier_names": ["Vietnam Plastics Jsc", "Manila Logistics Corp"]
    }
]

def fetch_sec_financial_signals(supplier_name: str) -> List[Dict[str, Any]]:
    """
    Simulates fetching financial health signals from SEC EDGAR or credit databases.
    Checks if a supplier name matches any known financial distress events.
    """
    events = []
    
    # In a real environment, we'd query SEC EDGAR CIK directories if the supplier is publicly traded.
    # For a private supplier or offline demo, we match on name or return a standard clean bill of health.
    supplier_lower = supplier_name.lower()
    
    for item in FALLBACK_FINANCIAL_REPORTS:
        matches = False
        for s in item["supplier_names"]:
            if s.lower() in supplier_lower:
                matches = True
                break
        if matches:
            copy_item = item.copy()
            copy_item["event_date"] = datetime.utcnow() - timedelta(days=4)
            copy_item.pop("supplier_names", None)  # Clean metadata
            events.append(copy_item)
            
    # If no negative events found, return a default stable financial status event
    if not events:
        events.append({
            "title": f"Stable Financial Profile for {supplier_name}",
            "evidence_text": f"Financial signal search indicates stable debt-to-equity ratio and adequate liquidity buffers. Operating margins remain within historical ranges.",
            "source_url": "https://www.sec.gov/edgar/mock/stable-profile",
            "source_name": "Public Filing Analysis",
            "severity": "low",
            "risk_type": "financial",
            "event_date": datetime.utcnow()
        })
        
    return events
