from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class ContingencyPlan(BaseModel):
    supplier_id: str = Field(..., description="Target supplier ID")
    trigger_event_id: str = Field(..., description="Risk event ID triggering this contingency plan")
    recommended_action: str = Field(..., description="Detailed recommended actions for mitigation")
    alternate_supplier_id: Optional[str] = Field(None, description="Recommended alternative supplier ID")
    proposed_volume_shift_percent: Optional[float] = Field(None, description="Proposed shift percentage of supply volume")
    estimated_lead_time_delta_days: Optional[int] = Field(None, description="Estimated delay delta impact in days")
    assumptions: List[str] = Field(default_factory=list, description="Explicit assumptions behind this plan")
    evidence_links: List[str] = Field(default_factory=list, description="Verification evidence source links")
    approval_status: Literal["draft", "approved", "rejected"] = Field(default="draft", description="Plan approval status")
