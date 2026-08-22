from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLog(BaseModel):
    log_id: str = Field(..., description="Unique log identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time of event")
    action_type: str = Field(..., description="Action performed: upload, check, review, approval, etc.")
    user_id: Optional[str] = Field(None, description="Initiating user if authenticated")
    details: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary details")
    status: str = Field(..., description="Success or Failure status")
