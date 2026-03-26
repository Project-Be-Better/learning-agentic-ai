"""
Structured logging for Agent Framework.

Outputs JSON logs compatible with ELK (Elasticsearch, Logstash, Kibana)
and PLG (Prometheus, Loki, Grafana) stacks.

Features:
- Structured JSON logging
- Correlation IDs for tracing
- Agent context (agent_id, trip_id)
- Performance metrics
- Error tracking
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class StructuredLogger:
    """Production-ready structured logger for monitoring and observability."""

    def __init__(self, name: str):
        """Initialize structured logger."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Console handler with JSON formatter
        handler = logging.StreamHandler()
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log(
        self,
        level: str,
        action: str,
        status: str,
        agent_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a structured event.

        Args:
            level: Log level (debug, info, warning, error, critical)
            action: What happened (e.g., "capsule_verified", "agent_executed")
            status: Result status (e.g., "success", "failure", "rejected")
            agent_id: Agent identifier
            trip_id: Trip identifier
            correlation_id: Request correlation ID for tracing
            duration_ms: Operation duration in milliseconds
            error: Error message if applicable
            details: Additional context dict
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "action": action,
            "status": status,
            "agent_id": agent_id,
            "trip_id": trip_id,
            "correlation_id": correlation_id,
            "duration_ms": duration_ms,
            "error": error,
        }

        # Merge additional details
        if details:
            log_entry.update(details)

        # Log at appropriate level
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_entry))

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.log("debug", message, **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.log("critical", message, **kwargs)


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # If message is already JSON (from our log method), return as-is
        if record.getMessage().startswith("{"):
            return record.getMessage()

        # Otherwise, wrap in JSON
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_entry)


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger."""
    return StructuredLogger(name)


class LogContext:
    """Context manager for timing and correlation."""

    def __init__(
        self,
        logger: StructuredLogger,
        action: str,
        agent_id: Optional[str] = None,
        trip_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        """Initialize log context."""
        self.logger = logger
        self.action = action
        self.agent_id = agent_id
        self.trip_id = trip_id
        self.correlation_id = correlation_id
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        self.logger.info(
            f"{self.action}_started",
            status="started",
            agent_id=self.agent_id,
            trip_id=self.trip_id,
            correlation_id=self.correlation_id,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log completion with duration."""
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            self.logger.error(
                f"{self.action}_failed",
                status="failed",
                agent_id=self.agent_id,
                trip_id=self.trip_id,
                correlation_id=self.correlation_id,
                duration_ms=duration_ms,
                error=str(exc_val),
            )
        else:
            self.logger.info(
                f"{self.action}_completed",
                status="success",
                agent_id=self.agent_id,
                trip_id=self.trip_id,
                correlation_id=self.correlation_id,
                duration_ms=duration_ms,
            )
