import logging
from src.graph.state import RiskMonitorState

logger = logging.getLogger(__name__)

def check_human_review_route(state: RiskMonitorState) -> str:
    """
    Decides if the assessment needs to pause for human review.
    """
    assessment = state.get("risk_assessment")
    
    if not assessment:
        logger.warning("No assessment found. Routing directly to end.")
        return "end"
        
    if assessment.human_review_required:
        logger.info(f"Risk assessment flags review required (Score: {assessment.overall_risk_score}). Routing to human_review_gate.")
        return "human_review_gate"
        
    logger.info("Risk assessment is low risk and clear. Routing to contingency_planning.")
    return "contingency_planning"

def check_review_decision_route(state: RiskMonitorState) -> str:
    """
    Determines route based on the human reviewer's action.
    """
    status = state.get("review_status", "pending")
    
    if status == "approved":
        logger.info("Review approved. Routing to contingency_planning.")
        return "contingency_planning"
    elif status == "rework":
        logger.info("Rework requested by reviewer. Routing back to profile_normalization.")
        return "profile_normalization"
    else:
        logger.info(f"Review status: {status}. Routing to end.")
        return "end"
