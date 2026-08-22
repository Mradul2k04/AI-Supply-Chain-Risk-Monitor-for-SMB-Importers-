import pytest
from guardrails.validators import validate_contingency_plan_rules
from src.schemas.contingency import ContingencyPlan

def test_validate_contingency_plan_rules_valid():
    # Arrange
    plan = ContingencyPlan(
        supplier_id="SUP001",
        trigger_event_id="evt_001",
        recommended_action="Actions",
        alternate_supplier_id="SUP003",
        proposed_volume_shift_percent=40.0,
        estimated_lead_time_delta_days=14,
        assumptions=[],
        evidence_links=[],
        approval_status="draft"
    )
    
    # Act
    errors = validate_contingency_plan_rules(plan, allowed_alternates=["SUP003", "SUP004"])
    
    # Assert
    assert len(errors) == 0

def test_validate_contingency_plan_rules_invalid_alternate():
    # Arrange
    plan = ContingencyPlan(
        supplier_id="SUP001",
        trigger_event_id="evt_001",
        recommended_action="Actions",
        alternate_supplier_id="SUP999",  # Not in allowed list
        proposed_volume_shift_percent=40.0,
        estimated_lead_time_delta_days=14,
        assumptions=[],
        evidence_links=[],
        approval_status="draft"
    )
    
    # Act
    errors = validate_contingency_plan_rules(plan, allowed_alternates=["SUP003", "SUP004"])
    
    # Assert
    assert len(errors) == 1
    assert "SUP999" in errors[0]

def test_validate_contingency_plan_rules_invalid_volume_shift():
    # Arrange
    plan = ContingencyPlan(
        supplier_id="SUP001",
        trigger_event_id="evt_001",
        recommended_action="Actions",
        alternate_supplier_id="SUP003",
        proposed_volume_shift_percent=150.0,  # Invalid shift (exceeds 100)
        estimated_lead_time_delta_days=14,
        assumptions=[],
        evidence_links=[],
        approval_status="draft"
    )
    
    # Act
    errors = validate_contingency_plan_rules(plan, allowed_alternates=["SUP003", "SUP004"])
    
    # Assert
    assert len(errors) == 1
    assert "150.0%" in errors[0]
