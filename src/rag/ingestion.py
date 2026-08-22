import logging
from datetime import datetime
from src.rag.chroma_client import get_chroma_manager

logger = logging.getLogger(__name__)

# Sample contingency playbooks
PLAYBOOKS = [
    {
        "id": "playbook_port_disruption_001",
        "text": "Port Congestion Playbook: If a primary shipping port faces cargo bottlenecks or strikes exceeding 3 days: 1. Evaluate alternate ports within 200 miles. 2. For critical shipments with lead time margin < 5 days, shift up to 40% of cargo volume to air freight. 3. Re-route remaining volume to secondary approved ports and adjust safety stock buffers upwards by 2 weeks.",
        "metadata": {
            "risk_type": "port_disruption",
            "severity": "high",
            "source_name": "Standard Contingency Playbooks V2",
            "source_url": "internal://playbooks/port_congestion",
            "license_status": "approved",
            "confidence": 1.0,
            "event_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "retrieval_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    },
    {
        "id": "playbook_weather_disruption_001",
        "text": "Weather Disruption Playbook: For hurricanes, severe monsoon floods, or winter freezes affecting regional supply hubs: 1. Suspend departures and secure warehouse inventory. 2. Activate local contingency safety stock. 3. Check alternate suppliers list for domestic backup sourcing. 4. Temporarily shift procurement orders to approved suppliers in low-risk zones.",
        "metadata": {
            "risk_type": "weather",
            "severity": "critical",
            "source_name": "Weather Risk Policy Guidelines",
            "source_url": "internal://playbooks/weather_emergency",
            "license_status": "approved",
            "confidence": 1.0,
            "event_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "retrieval_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    },
    {
        "id": "playbook_financial_disruption_001",
        "text": "Financial Distress Playbook: For supplier liquidity warnings, debt restructurings, or credit rating downgrades: 1. Trigger an immediate financial audit of the vendor. 2. Initiate validation of alternate supplier options. 3. Reduce purchase order volumes by 20% to mitigate exposure. 4. Do not issue advance payments. 5. Set up secondary supplier contract agreements.",
        "metadata": {
            "risk_type": "financial",
            "severity": "high",
            "source_name": "Financial Risk Mitigation Rules",
            "source_url": "internal://playbooks/financial_distress",
            "license_status": "approved",
            "confidence": 1.0,
            "event_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "retrieval_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
]

# Regional Risk Profiles
REGIONAL_RISKS = [
    {
        "id": "region_cn_shanghai_001",
        "text": "East China Regional Profile: High concentration of electronics and ceramics manufacturing. Shipping lanes through Port of Shanghai are susceptible to seasonal typhoon disruptions between July and September. Geopolitical regulatory shifts can result in sudden export tariff hikes.",
        "metadata": {
            "country": "China",
            "city_or_region": "Shanghai",
            "port": "Port of Shanghai",
            "risk_type": "geopolitical",
            "severity": "medium",
            "source_name": "Regional Intelligence Desk",
            "source_url": "internal://regions/east_china",
            "license_status": "approved",
            "confidence": 0.9,
            "event_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "retrieval_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    },
    {
        "id": "region_vn_hcmc_001",
        "text": "South Vietnam Regional Profile: Fast-growing hub for textile and plastic suppliers. High exposure to extreme monsoon rainfall and localized urban flooding that delays inland logistics. Port of Cat Lai experiences container processing queues during peak export seasons.",
        "metadata": {
            "country": "Vietnam",
            "city_or_region": "Ho Chi Minh City",
            "port": "Port of Cat Lai",
            "risk_type": "weather",
            "severity": "medium",
            "source_name": "ASEAN Trade Report",
            "source_url": "internal://regions/south_vietnam",
            "license_status": "approved",
            "confidence": 0.85,
            "event_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "retrieval_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
]

def ingest_default_knowledge_base():
    """Ingests static playbooks and regional intelligence reports into ChromaDB."""
    logger.info("Starting ChromaDB knowledge base ingestion...")
    manager = get_chroma_manager()
    
    # 1. Ingest Playbooks
    playbook_col = manager.get_collection("contingency_playbooks")
    for pb in PLAYBOOKS:
        playbook_col.upsert(
            ids=[pb["id"]],
            documents=[pb["text"]],
            metadatas=[pb["metadata"]]
        )
    logger.info(f"Ingested {len(PLAYBOOKS)} contingency playbooks.")

    # 2. Ingest Regional Risks
    regional_col = manager.get_collection("regional_risk_profiles")
    for r in REGIONAL_RISKS:
        regional_col.upsert(
            ids=[r["id"]],
            documents=[r["text"]],
            metadatas=[r["metadata"]]
        )
    logger.info(f"Ingested {len(REGIONAL_RISKS)} regional risk profiles.")
