import os
import yaml
import logging
from typing import List
from src.schemas.risk_event import RiskEvent
from src.schemas.assessment import SupplierRiskAssessment

logger = logging.getLogger(__name__)

RULES_PATH = "guardrails/risk_scoring_rules.yaml"

DEFAULT_WEIGHTS = {
    "geopolitical": 0.25,
    "weather": 0.20,
    "earthquake": 0.15,
    "port_disruption": 0.20,
    "financial": 0.10,
    "logistics": 0.10
}

SEVERITY_SCORES = {
    "low": 2.0,
    "medium": 5.0,
    "high": 8.0,
    "critical": 10.0
}

def load_scoring_rules() -> dict:
    if os.path.exists(RULES_PATH):
        try:
            with open(RULES_PATH, 'r') as f:
                config = yaml.safe_load(f)
                if config and "weights" in config:
                    logger.info("Loaded weights from risk_scoring_rules.yaml")
                    return config["weights"]
        except Exception as e:
            logger.warning(f"Failed to load risk_scoring_rules.yaml: {e}. Using defaults.")
    return DEFAULT_WEIGHTS

def calculate_supplier_risk(supplier_id: str, events: List[RiskEvent], product_categories: List[str]) -> SupplierRiskAssessment:
    """
    Computes a composite weighted risk score for a supplier based on active risk events.
    """
    weights = load_scoring_rules()
    
    # Track the highest severity score for each risk type
    max_scores = {risk_type: 0.0 for risk_type in weights.keys()}
    contributing_ids = []
    
    for event in events:
        risk_type = event.risk_type
        if risk_type in max_scores:
            sev_score = SEVERITY_SCORES.get(event.severity, 0.0)
            # Update to keep the highest severity event of this type
            if sev_score > max_scores[risk_type]:
                max_scores[risk_type] = sev_score
            contributing_ids.append(event.event_id)
            
    # Calculate weighted score (scale 0-10)
    weighted_sum = 0.0
    weight_total = 0.0
    for r_type, max_score in max_scores.items():
        weight = weights.get(r_type, 0.0)
        # We always apply weight, but if max_score is 0, we treat it as 0.0 (minimal/no threat)
        weighted_sum += max_score * weight
        weight_total += weight
        
    final_score = (weighted_sum / weight_total) * 10.0 if weight_total > 0 else 0.0
    # Round to 1 decimal place
    final_score = round(min(max(final_score, 0.0), 100.0), 1)
    
    # Classify qualitative risk level using env thresholds
    high_threshold = float(os.getenv("HIGH_RISK_THRESHOLD", "80"))
    med_threshold = float(os.getenv("MEDIUM_RISK_THRESHOLD", "60"))
    low_threshold = float(os.getenv("LOW_RISK_THRESHOLD", "30"))
    require_approval = os.getenv("REQUIRE_HUMAN_APPROVAL", "true").lower() == "true"
    
    if final_score >= high_threshold:
        risk_level = "critical"
    elif final_score >= med_threshold:
        risk_level = "high"
    elif final_score >= low_threshold:
        risk_level = "medium"
    else:
        risk_level = "low"
        
    # Determine if human review is required
    if require_approval:
        human_review_required = final_score >= med_threshold or any(e.severity in ["high", "critical"] for e in events)
    else:
        human_review_required = False
    
    # Summarize operational impact
    if events:
        impacts = [f"{e.title} ({e.severity.upper()})" for e in events]
        operational_impact = "Potential logistics bottleneck caused by: " + "; ".join(impacts)
    else:
        operational_impact = "No active risk events. Operations running normally."
        
    # Average confidence of contributing events, or default to 1.0 if clear
    avg_confidence = sum(e.confidence for e in events) / len(events) if events else 1.0
    
    return SupplierRiskAssessment(
        supplier_id=supplier_id,
        overall_risk_score=final_score,
        risk_level=risk_level,
        contributing_events=contributing_ids,
        affected_products=product_categories,
        operational_impact=operational_impact,
        confidence=round(avg_confidence, 2),
        human_review_required=human_review_required
    )
