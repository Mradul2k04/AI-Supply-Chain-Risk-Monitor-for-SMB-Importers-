from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class RiskEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    risk_type: Literal[
        "geopolitical", "weather", "earthquake",
        "port_disruption", "financial", "logistics"
    ] = Field(..., description="Specific risk classification")
    title: str = Field(..., description="Short summary title of the event")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Severity classification")
    event_date: datetime = Field(..., description="When the event occurred or was reported")
    region: str = Field(..., description="Geographical area affected")
    source_url: str = Field(..., description="URL source link for evidence verification")
    source_name: str = Field(..., description="Name of the source reporting the event")
    evidence_text: str = Field(..., description="Snippet/evidence showing the impact description")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
