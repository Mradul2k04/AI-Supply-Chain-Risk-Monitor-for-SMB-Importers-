from pydantic import BaseModel, Field
from typing import List, Literal

class SupplierRiskAssessment(BaseModel):
    supplier_id: str = Field(..., description="Target supplier ID")
    overall_risk_score: float = Field(..., description="Overall calculated weighted risk score")
    risk_level: Literal["low", "medium", "high", "critical"] = Field(..., description="Qualitative risk classification")
    contributing_events: List[str] = Field(default_factory=list, description="IDs of contributing risk events")
    affected_products: List[str] = Field(default_factory=list, description="Products affected by the disruption")
    operational_impact: str = Field(..., description="Description of the operational disruption")
    confidence: float = Field(..., description="Overall confidence level of risk assessment")
    human_review_required: bool = Field(default=False, description="Flag indicating review is required before action")
