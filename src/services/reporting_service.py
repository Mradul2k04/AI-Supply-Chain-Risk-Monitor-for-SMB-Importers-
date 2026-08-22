import os
import json
import csv
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

EXPORT_DIR = os.getenv("EXPORT_DIR", "data/exports")

def export_risk_report(report_data: List[Dict[str, Any]], format_type: str = "json") -> str:
    """
    Exports the compiled risk report data into the specified format (json/csv).
    Returns the file path of the exported report.
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"risk_report_{timestamp}.{format_type}"
    file_path = os.path.join(EXPORT_DIR, file_name)
    
    try:
        if format_type == "json":
            with open(file_path, "w") as f:
                json.dump(report_data, f, indent=4, default=str)
        elif format_type == "csv":
            if not report_data:
                return file_path
                
            headers = report_data[0].keys()
            with open(file_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for row in report_data:
                    # Format lists and dicts as strings for CSV compatibility
                    cleaned_row = {}
                    for k, v in row.items():
                        if isinstance(v, (list, dict)):
                            cleaned_row[k] = json.dumps(v)
                        else:
                            cleaned_row[k] = v
                    writer.writerow(cleaned_row)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")
            
        logger.info(f"Successfully exported report to: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error exporting report: {e}", exc_info=True)
        raise
