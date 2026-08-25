import os
import sqlite3
import logging
from typing import Dict, Any, List
from src.config.settings import settings
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import RiskMonitorState
from src.graph.routing import check_human_review_route, check_review_decision_route

# Import Agent runs
from src.agents.supplier_profile_agent import run_supplier_profile_agent
from src.agents.risk_intelligence_agent import run_risk_intelligence_agent
from src.agents.weather_disaster_agent import run_weather_disaster_agent
from src.agents.financial_signal_agent import run_financial_signal_agent
from src.agents.risk_scoring_agent import run_risk_scoring_agent
from src.agents.contingency_agent import run_contingency_planner_agent
from src.agents.report_writer_agent import run_report_writer_agent

# Import DB/Service Layer
from src.services.database import SessionLocal, init_db
from src.services.supplier_service import upsert_supplier
from src.services.alert_service import save_risk_event
from src.services.contingency_service import save_contingency_plan

logger = logging.getLogger(__name__)

# Node functions
def profile_normalization_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Supplier Profile Normalization ---")
    supplier = run_supplier_profile_agent(state["supplier_input"])
    
    # Save supplier to SQL DB
    db = SessionLocal()
    try:
        upsert_supplier(db, supplier)
    finally:
        db.close()
        
    return {"supplier": supplier}

def collect_geopolitical_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Geopolitical Signals Collection ---")
    supplier = state["supplier"]
    events = run_risk_intelligence_agent(
        supplier_name=supplier.name,
        country=supplier.country,
        region=supplier.city_or_region,
        port=supplier.primary_port
    )
    return {"geopolitical_events": events}

def collect_weather_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Weather & Disaster Signals Collection ---")
    supplier = state["supplier"]
    events = run_weather_disaster_agent(
        supplier_id=supplier.supplier_id,
        country=supplier.country,
        city_or_region=supplier.city_or_region,
        lat=supplier.latitude,
        lon=supplier.longitude
    )
    return {"weather_events": events}

def collect_financial_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Public Financial Signals Collection ---")
    supplier = state["supplier"]
    events = run_financial_signal_agent(supplier_name=supplier.name)
    return {"financial_events": events}

def evidence_retrieval_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Evidence Retrieval & Merging ---")
    # Combine parallel events
    all_events = []
    all_events.extend(state.get("geopolitical_events", []))
    all_events.extend(state.get("weather_events", []))
    all_events.extend(state.get("financial_events", []))
    
    # Save active events to SQL DB
    db = SessionLocal()
    try:
        for event in all_events:
            save_risk_event(db, event)
    finally:
        db.close()
        
    return {"all_events": all_events}

def risk_scoring_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Risk Scoring ---")
    supplier = state["supplier"]
    events = state["all_events"]
    
    assessment = run_risk_scoring_agent(supplier, events)
    return {"risk_assessment": assessment}

def human_review_gate_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Human Review Gate ---")
    # This is a synchronization barrier checkpoint.
    # The application pauses here and waits for user decision updates before proceeding.
    return {}

def contingency_planning_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Contingency Planning ---")
    supplier = state["supplier"]
    events = state["all_events"]
    
    # Reuse previewed/stored plans if already present to prevent duplicate agent execution
    existing_plans = state.get("contingency_plans")
    if existing_plans:
        logger.info(f"Reusing {len(existing_plans)} existing previewed contingency plans without re-generation.")
        db = SessionLocal()
        try:
            for plan in existing_plans:
                save_contingency_plan(db, plan)
        finally:
            db.close()
        return {"contingency_plans": existing_plans}

    plans = []
    # Generate contingency plans for medium/high/critical events
    for event in events:
        if str(event.severity).lower() in ["medium", "high", "critical"]:
            plan = run_contingency_planner_agent(supplier, event)
            plans.append(plan)
            
            # Save draft plan to DB
            db = SessionLocal()
            try:
                save_contingency_plan(db, plan)
            finally:
                db.close()
                
    return {"contingency_plans": plans}

def report_writing_node(state: RiskMonitorState) -> Dict[str, Any]:
    logger.info("--- NODE: Report Writing ---")
    supplier = state["supplier"]
    assessment = state["risk_assessment"]
    plans = state["contingency_plans"]
    
    report = run_report_writer_agent(supplier, assessment, plans)
    return {"compiled_report": report}

# Build workflow graph
workflow = StateGraph(RiskMonitorState)

# Add Nodes
workflow.add_node("profile_normalization", profile_normalization_node)
workflow.add_node("collect_geopolitical", collect_geopolitical_node)
workflow.add_node("collect_weather", collect_weather_node)
workflow.add_node("collect_financial", collect_financial_node)
workflow.add_node("evidence_retrieval", evidence_retrieval_node)
workflow.add_node("risk_scoring", risk_scoring_node)
workflow.add_node("human_review_gate", human_review_gate_node)
workflow.add_node("contingency_planning", contingency_planning_node)
workflow.add_node("report_writing", report_writing_node)

# Set Up Directed Edges
workflow.add_edge(START, "profile_normalization")

# Fork parallel collect nodes
workflow.add_edge("profile_normalization", "collect_geopolitical")
workflow.add_edge("profile_normalization", "collect_weather")
workflow.add_edge("profile_normalization", "collect_financial")

# Join parallel collect nodes
workflow.add_edge("collect_geopolitical", "evidence_retrieval")
workflow.add_edge("collect_weather", "evidence_retrieval")
workflow.add_edge("collect_financial", "evidence_retrieval")

workflow.add_edge("evidence_retrieval", "risk_scoring")

# Conditional Router from Risk Scoring
workflow.add_conditional_edges(
    "risk_scoring",
    check_human_review_route,
    {
        "human_review_gate": "human_review_gate",
        "contingency_planning": "contingency_planning",
        "end": END
    }
)

# Conditional Router from Human Gate
workflow.add_conditional_edges(
    "human_review_gate",
    check_review_decision_route,
    {
        "contingency_planning": "contingency_planning",
        "profile_normalization": "profile_normalization",
        "end": END
    }
)

workflow.add_edge("contingency_planning", "report_writing")
workflow.add_edge("report_writing", END)

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

CUSTOM_MSG_PACK_MODULES = [
    ("src.schemas.supplier", "Supplier"),
    ("src.schemas.risk_event", "RiskEvent"),
    ("src.schemas.assessment", "SupplierRiskAssessment"),
    ("src.schemas.contingency", "ContingencyPlan")
]

def create_smart_checkpointer():
    """
    Initializes the optimal LangGraph checkpointer:
    - Thread-safe PostgresSaver with ConnectionPool for production/Railway when PostgreSQL is accessible
    - Persistent SqliteSaver for disk-backed persistence in local development
    - MemorySaver as safety fallback
    """
    custom_serde = JsonPlusSerializer(allowed_msgpack_modules=CUSTOM_MSG_PACK_MODULES)

    # 1. Try SQLite Checkpointer (Disk persistent)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        db_dir = "data"
        os.makedirs(db_dir, exist_ok=True)
        sqlite_path = os.path.join(db_dir, "langgraph_checkpoints.db")
        conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn, serde=custom_serde)
        checkpointer.setup()
        logger.info(f"Successfully initialized persistent SQLite LangGraph Checkpointer at '{sqlite_path}'.")
        return checkpointer
    except Exception as e:
        logger.debug(f"SqliteSaver checkpointer info: {e}")

    # 2. Try PostgreSQL Checkpointer if configured
    if settings.DATABASE_URL.startswith("postgresql"):
        try:
            from psycopg_pool import ConnectionPool
            from langgraph.checkpoint.postgres import PostgresSaver
            
            pool = ConnectionPool(settings.DATABASE_URL, max_size=20, kwargs={"connect_timeout": 10})
            checkpointer = PostgresSaver(pool, serde=custom_serde)
            try:
                checkpointer.setup()
            except Exception:
                pass
            logger.info("Successfully initialized thread-safe PostgreSQL LangGraph Checkpointer.")
            return checkpointer
        except Exception as e:
            logger.debug(f"PostgresSaver connection info: {e}")

    # 3. MemorySaver fallback
    logger.info("Initialized MemorySaver LangGraph Checkpointer.")
    return MemorySaver()

# Compile graph with Smart Persistent Checkpointer and interrupts
memory = create_smart_checkpointer()
app_graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review_gate"]
)

def initialize_system():
    """Initializes schema and runs any initial DB configuration."""
    init_db()
