"""
Structured logging configuration with JSON formatting for production observability.
"""
import logging
import sys
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """Formats log records as JSON objects for SIEM / Datadog / CloudWatch ingestion."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)

def setup_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("incident_platform")
    logger.setLevel(level)
    logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger

logger = setup_logging()
