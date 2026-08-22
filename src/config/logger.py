import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import List, Dict, Any, Optional
from src.config.settings import settings

LOG_DIR = "logs"
APP_LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging():
    """
    Sets up application wide logging config.
    Outputs to console stderr and a single app.log file.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Parse Log Level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = level_map.get(settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Define log format
    log_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] - %(message)s"
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to prevent double logs in Streamlit
    if root_logger.handlers:
        root_logger.handlers.clear()
        
    # Console stream handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Main single rotating file handler
    file_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB per log file limit
        backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Disable logs noise from third-party libraries unless debug
    if log_level != logging.DEBUG:
        for lib in ["urllib3", "requests", "chromadb", "openai", "httpcore", "huggingface_hub"]:
            logging.getLogger(lib).setLevel(logging.WARNING)
            
    logging.info(f"Logging initialized. Level: {settings.LOG_LEVEL}, file: {APP_LOG_FILE}")
    log_production_stage("SYSTEM_INIT", "SUCCESS", "Logging subsystem operational.")

def log_production_stage(stage_name: str, status: str, details: str = ""):
    """
    Logs a high-level production milestone checkpoint into app.log.
    """
    msg = f"[PROD_CHECKPOINT] Stage: {stage_name} | Status: {status}"
    if details:
        msg += f" | Details: {details}"
    logger = logging.getLogger("production_monitor")
    logger.info(msg)

def get_recent_logs(max_lines: int = 200, level_filter: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Reads and parses the most recent log entries from app.log.
    """
    if not os.path.exists(APP_LOG_FILE):
        return []
        
    parsed_logs = []
    try:
        with open(APP_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            
        selected_lines = lines[-max_lines:]
        for line in reversed(selected_lines):
            line_str = line.strip()
            if not line_str:
                continue
                
            if search_query and search_query.lower() not in line_str.lower():
                continue
                
            parts = line_str.split(" - ", 1)
            msg = parts[1] if len(parts) > 1 else line_str
            meta = parts[0] if len(parts) > 1 else ""
            
            level = "INFO"
            for lvl in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]:
                if lvl in meta:
                    level = lvl
                    break
                    
            if level_filter and level_filter.upper() != "ALL" and level != level_filter.upper():
                continue
                
            parsed_logs.append({
                "raw": line_str,
                "timestamp": meta.split("]")[0].replace("[", "") if "[" in meta else "",
                "level": level,
                "meta": meta,
                "message": msg
            })
    except Exception as e:
        logging.error(f"Error reading log file {APP_LOG_FILE}: {e}")
        
    return parsed_logs

def get_production_status_summary() -> Dict[str, Any]:
    """
    Summarizes production execution health and error counts from app.log.
    """
    logs = get_recent_logs(max_lines=500)
    
    error_count = sum(1 for l in logs if l["level"] in ["ERROR", "CRITICAL"])
    warning_count = sum(1 for l in logs if l["level"] == "WARNING")
    info_count = sum(1 for l in logs if l["level"] == "INFO")
    
    last_checkpoint = "INITIALIZING"
    for pl in logs:
        if "[PROD_CHECKPOINT]" in pl["message"] or "[PROD_CHECKPOINT]" in pl["raw"]:
            last_checkpoint = pl["message"]
            break
            
    return {
        "log_file": APP_LOG_FILE,
        "total_parsed": len(logs),
        "errors": error_count,
        "warnings": warning_count,
        "info": info_count,
        "last_checkpoint": last_checkpoint,
        "status": "HEALTHY" if error_count == 0 else ("DEGRADED" if error_count < 5 else "CRITICAL")
    }

# Auto-initialize on import
setup_logging()


