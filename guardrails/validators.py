import os
import yaml
import logging
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

ALLOWLIST_PATH = "guardrails/source_allowlist.yaml"

def load_source_allowlist() -> Dict[str, List[str]]:
    if os.path.exists(ALLOWLIST_PATH):
        try:
            with open(ALLOWLIST_PATH, 'r') as f:
                config = yaml.safe_load(f)
                if config and "allowed_sources" in config:
                    return config["allowed_sources"]
        except Exception as e:
            logger.warning(f"Failed to load source_allowlist.yaml: {e}")
    return {}

def validate_source_url(url: str, category: str) -> bool:
    """Checks if a URL belongs to the allowed domains for a given category."""
    if not url:
        return False
        
    # Support mock internal protocols
    if url.startswith("internal://"):
        return True
        
    allowlist = load_source_allowlist()
    allowed_domains = allowlist.get(category, [])
    
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        if not domain:
            domain = parsed_url.path.lower()  # handle format without scheme
            
        # Check if domain or parent domain matches any allowed domain
        for allowed in allowed_domains:
            if domain == allowed or domain.endswith("." + allowed):
                return True
    except Exception as e:
        logger.error(f"Error parsing URL '{url}': {e}")
        
    return False

def validate_contingency_plan_rules(
    plan: Any,
    allowed_alternates: List[str]
) -> List[str]:
    """
    Validates business rules for a contingency plan:
    1. Returns error if alternate supplier is not on the allowed_alternates list.
    2. Checks volume shift bounds (0% to 100%).
    """
    errors = []
    
    # Alternate supplier verification
    if plan.alternate_supplier_id:
        if plan.alternate_supplier_id not in allowed_alternates:
            errors.append(
                f"Validation Error: Alternate supplier '{plan.alternate_supplier_id}' "
                f"is not in the approved alternate supplier list: {allowed_alternates}"
            )
            
    # Volume shift verification
    if plan.proposed_volume_shift_percent is not None:
        if not (0.0 <= plan.proposed_volume_shift_percent <= 100.0):
            errors.append(
                f"Validation Error: Proposed volume shift percentage "
                f"({plan.proposed_volume_shift_percent}%) must be between 0.0 and 100.0."
            )
            
    return errors

def validate_pydantic_schema(model_class: type[BaseModel], data: Dict[str, Any]) -> Optional[str]:
    """Validates data dictionary against a Pydantic model class."""
    try:
        model_class(**data)
        return None
    except ValidationError as e:
        return str(e)
