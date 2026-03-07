"""Structured logging setup."""
import logging
import json
from datetime import datetime
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "job_id"):
            log_data["job_id"] = record.job_id
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage
        if hasattr(record, "doc_id"):
            log_data["doc_id"] = record.doc_id
        if hasattr(record, "elapsed_ms"):
            log_data["elapsed_ms"] = record.elapsed_ms

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Setup structured logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
