import pytest
from src.graph.routing import check_human_review_route, check_review_decision_route
from src.schemas.assessment import SupplierRiskAssessment

def test_check_human_review_route_low_risk():
    # Arrange
    state = {
        "risk_assessment": SupplierRiskAssessment(
            supplier_id="SUP001",
            overall_risk_score=15.0,
            risk_level="low",
            contributing_events=[],
            affected_products=["Ceramics"],
            operational_impact="No threat",
            confidence=1.0,
            human_review_required=False
        )
    }
    
    # Act
    route = check_human_review_route(state)
    
    # Assert
    assert route == "contingency_planning"

def test_check_human_review_route_high_risk():
    # Arrange
    state = {
        "risk_assessment": SupplierRiskAssessment(
            supplier_id="SUP002",
            overall_risk_score=65.0,
            risk_level="high",
            contributing_events=["evt_001"],
            affected_products=["Electronics"],
            operational_impact="High risk",
            confidence=0.9,
            human_review_required=True
        )
    }
    
    # Act
    route = check_human_review_route(state)
    
    # Assert
    assert route == "human_review_gate"

def test_check_review_decision_route_approved():
    # Arrange
    state = {"review_status": "approved"}
    
    # Act
    route = check_review_decision_route(state)
    
    # Assert
    assert route == "contingency_planning"

def test_check_review_decision_route_rework():
    # Arrange
    state = {"review_status": "rework"}
    
    # Act
    route = check_review_decision_route(state)
    
    # Assert
    assert route == "profile_normalization"
