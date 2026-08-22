import os
import pytest
from datetime import datetime
from src.schemas.risk_event import RiskEvent
from src.services.scoring_service import calculate_supplier_risk

def test_risk_scoring_no_events():
    # Arrange
    os.environ["LOW_RISK_THRESHOLD"] = "25.0"
    os.environ["MEDIUM_RISK_THRESHOLD"] = "50.0"
    os.environ["HIGH_RISK_THRESHOLD"] = "75.0"
    os.environ["REQUIRE_HUMAN_APPROVAL"] = "true"
    
    # Act
    assessment = calculate_supplier_risk(
        supplier_id="SUP001",
        events=[],
        product_categories=["Ceramics"]
    )
    
    # Assert
    assert assessment.overall_risk_score == 0.0
    assert assessment.risk_level == "low"
    assert assessment.human_review_required is False

def test_risk_scoring_critical_event():
    # Arrange
    os.environ["LOW_RISK_THRESHOLD"] = "25.0"
    os.environ["MEDIUM_RISK_THRESHOLD"] = "50.0"
    os.environ["HIGH_RISK_THRESHOLD"] = "75.0"
    os.environ["REQUIRE_HUMAN_APPROVAL"] = "true"
    
    events = [
        RiskEvent(
            event_id="evt_001",
            risk_type="geopolitical",
            title="Suez Canal Blocked",
            severity="critical",
            event_date=datetime.utcnow(),
            region="Suez",
            source_url="https://gdeltproject.org/mock/suez",
            source_name="GDELT",
            evidence_text="Blocked shipping lanes.",
            confidence=0.9
        )
    ]
    
    # Act
    assessment = calculate_supplier_risk(
        supplier_id="SUP002",
        events=events,
        product_categories=["Electronics"]
    )
    
    # Assert
    # Weighted calculation: max geopolitical score = 10.0 (critical), weight = 0.25
    # Since other categories are 0, weighted sum is (10.0 * 0.25) = 2.5. Total weights = 1.0.
    # Score = 2.5 * 10 = 25.0
    assert assessment.overall_risk_score == 25.0
    assert assessment.risk_level == "medium"
    assert assessment.human_review_required is True  # Critical event forces human review
