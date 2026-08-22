from pydantic import BaseModel, Field
from typing import List, Optional

class Supplier(BaseModel):
    supplier_id: str = Field(..., description="Unique supplier identifier")
    name: str = Field(..., description="Supplier company name")
    country: str = Field(..., description="Country of operations")
    city_or_region: Optional[str] = Field(None, description="City or regional territory")
    latitude: Optional[float] = Field(None, description="Geocoded latitude coordinate")
    longitude: Optional[float] = Field(None, description="Geocoded longitude coordinate")
    product_categories: List[str] = Field(default_factory=list, description="Categories of products supplied")
    primary_port: Optional[str] = Field(None, description="Primary shipping port used")
    dependency_percent: Optional[float] = Field(None, description="Percentage dependency on this supplier")
    lead_time_days: Optional[int] = Field(None, description="Standard shipment lead time in days")
    approved_alternate_supplier_ids: List[str] = Field(default_factory=list, description="Approved backup supplier IDs")
