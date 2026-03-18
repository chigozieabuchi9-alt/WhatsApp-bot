"""
Structured logging configuration for the application.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer

from app.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if settings.LOG_FORMAT == "json":
        formatter = JSONRenderer()
    else:
        formatter = structlog.dev.ConsoleRenderer()
    
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )
    
    # Set third-party loggers to WARNING
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_request(
    logger: structlog.stdlib.BoundLogger,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    extra: Dict[str, Any] = None,
) -> None:
    """Log an HTTP request with structured data."""
    log_data = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
    }
    if extra:
        log_data.update(extra)
    
    if status_code >= 500:
        logger.error("http_request", **log_data)
    elif status_code >= 400:
        logger.warning("http_request", **log_data)
    else:
        logger.info("http_request", **log_data)
