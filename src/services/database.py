import os
import json
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from src.config.settings import settings

DATABASE_URL = settings.DATABASE_URL

logger = logging.getLogger(__name__)

# Configure DB Engine with fallback
try:
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    else:
        # Try creating engine and executing a simple test connection
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            pass
        logger.info("Successfully connected to the configured database.")
except Exception as e:
    logger.warning(
        f"Failed to connect to primary database ({DATABASE_URL}): {e}. "
        f"Reverting to local SQLite database (sqlite:///./supply_chain_risk.db) for safety."
    )
    fallback_url = "sqlite:///./supply_chain_risk.db"
    engine = create_engine(fallback_url, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DBSupplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    city_or_region = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    product_categories = Column(JSON, nullable=False, default=list)  # Stored as JSON list
    primary_port = Column(String, nullable=True)
    dependency_percent = Column(Float, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    approved_alternate_supplier_ids = Column(JSON, nullable=False, default=list)  # Stored as JSON list

class DBRiskEvent(Base):
    __tablename__ = "risk_events"

    event_id = Column(String, primary_key=True, index=True)
    risk_type = Column(String, nullable=False)  # geopolitical, weather, earthquake, port_disruption, financial, logistics
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # low, medium, high, critical
    event_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    region = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    source_name = Column(String, nullable=False)
    evidence_text = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)

class DBSupplierRiskAssessment(Base):
    __tablename__ = "supplier_risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.supplier_id"), nullable=False)
    overall_risk_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)  # low, medium, high, critical
    contributing_events = Column(JSON, nullable=False, default=list)  # JSON list of event_ids
    affected_products = Column(JSON, nullable=False, default=list)  # JSON list of products
    operational_impact = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    human_review_required = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("DBSupplier")

class DBContingencyPlan(Base):
    __tablename__ = "contingency_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, ForeignKey("suppliers.supplier_id"), nullable=False)
    trigger_event_id = Column(String, ForeignKey("risk_events.event_id"), nullable=False)
    recommended_action = Column(Text, nullable=False)
    alternate_supplier_id = Column(String, nullable=True)
    proposed_volume_shift_percent = Column(Float, nullable=True)
    estimated_lead_time_delta_days = Column(Integer, nullable=True)
    assumptions = Column(JSON, nullable=False, default=list)  # JSON list
    evidence_links = Column(JSON, nullable=False, default=list)  # JSON list
    approval_status = Column(String, nullable=False, default="draft")  # draft, approved, rejected
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    supplier = relationship("DBSupplier")
    trigger_event = relationship("DBRiskEvent")

class DBAuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    action_type = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    details = Column(JSON, nullable=False, default=dict)
    status = Column(String, nullable=False)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
