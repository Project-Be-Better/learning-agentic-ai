import logging
import os

_DEFAULT_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging() -> None:
    """Configure root logging once for local scripts and demos."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    level_name = os.getenv("TRACEDATA_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format=_DEFAULT_FORMAT,
    )


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Return a namespaced logger for TraceData agents."""
    setup_logging()
    return logging.getLogger(f"tracedata.agents.{agent_name}")
