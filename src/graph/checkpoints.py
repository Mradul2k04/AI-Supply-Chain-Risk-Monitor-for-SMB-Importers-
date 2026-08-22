import logging
from typing import Dict, Any, Optional
from src.graph.workflow import app_graph
from src.graph.state import RiskMonitorState

logger = logging.getLogger(__name__)

def run_risk_monitor_workflow(supplier_input: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
    """
    Kicks off the risk monitor graph flow for a given supplier profile input.
    If the graph hits an interrupt, it will return the state at the interrupt checkpoint.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Initialize state values
    initial_state = {
        "supplier_input": supplier_input,
        "supplier": None,
        "geopolitical_events": [],
        "weather_events": [],
        "financial_events": [],
        "all_events": [],
        "risk_assessment": None,
        "contingency_plans": [],
        "compiled_report": None,
        "review_status": "pending",
        "review_feedback": None
    }
    
    logger.info(f"Starting workflow for supplier: {supplier_input.get('name')} (Thread ID: {thread_id})")
    
    # Run the graph
    events = app_graph.stream(initial_state, config, stream_mode="values")
    final_state = None
    for event in events:
        final_state = event
        
    return final_state

def get_workflow_state(thread_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the current state checkpoint for a given thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_info = app_graph.get_state(config)
    if state_info:
        return state_info.values
    return None

def resume_workflow_with_decision(
    thread_id: str,
    status: str,  # "approved", "rejected", "rework"
    feedback: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates the state checkpoint with human review choices and resumes execution.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    logger.info(f"Resuming thread {thread_id} with status={status}, feedback={feedback}")
    
    # Update the thread state values
    app_graph.update_state(
        config,
        {"review_status": status, "review_feedback": feedback},
        as_node="human_review_gate"
    )
    
    # Continue graph execution from the interrupt checkpoint
    events = app_graph.stream(None, config, stream_mode="values")
    final_state = None
    for event in events:
        final_state = event
        
    return final_state
