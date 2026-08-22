import uuid
import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from src.services.database import SessionLocal, DBAuditLog

logger = logging.getLogger(__name__)

def get_or_create_session_id() -> str:
    """
    Retrieves the active session ID from st.query_params or generates a new one.
    This session ID persists across browser tab reloads.
    """
    # Try to read session_id from URL query params
    params = st.query_params
    session_id = params.get("session_id")
    
    if not session_id:
        # Generate new unique session ID
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        st.query_params["session_id"] = session_id
        logger.info(f"Generated new browser session ID: {session_id}")
    else:
        logger.debug(f"Re-using active browser session ID: {session_id}")
        
    return session_id

def add_session_message(db: Session, session_id: str, message: str, level: str = "info"):
    """
    Adds a message log associated with the active session to the database.
    """
    log_id = f"log_{uuid.uuid4().hex[:12]}"
    db_log = DBAuditLog(
        log_id=log_id,
        timestamp=datetime.utcnow(),
        action_type="session_message",
        user_id=session_id,  # Associate with session ID
        details={"message": message, "level": level},
        status="success"
    )
    db.add(db_log)
    db.commit()
    logger.info(f"Logged session message [{level}]: {message}")

def get_session_messages(db: Session, session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all log messages stored for the active session.
    """
    db_logs = db.query(DBAuditLog).filter(
        DBAuditLog.action_type == "session_message",
        DBAuditLog.user_id == session_id
    ).order_by(DBAuditLog.timestamp.asc()).all()
    
    messages = []
    for log in db_logs:
        details = log.details or {}
        messages.append({
            "timestamp": log.timestamp,
            "message": details.get("message", ""),
            "level": details.get("level", "info")
        })
    return messages

def clear_session_messages(db: Session, session_id: str):
    """
    Deletes all messages for a session.
    """
    db.query(DBAuditLog).filter(
        DBAuditLog.action_type == "session_message",
        DBAuditLog.user_id == session_id
    ).delete()
    db.commit()
