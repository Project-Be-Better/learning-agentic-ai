from enum import IntEnum, Enum


# ROUTING & QUEUE ENUMS


class Priority(IntEnum):
    """
    Routing priority for Celery queues.
    Lower number = higher priority.
    """

    CRITICAL = 0
    HIGH = 3
    MEDIUM = 6
    LOW = 9


class Queue(str, Enum):
    """Celery queue names. One queue per agent."""

    INGESTION = "ingestion_queue"
    SAFETY = "safety_queue"
    SCORING = "scoring_queue"
    SENTIMENT = "sentiment_queue"


class AgentName(str, Enum):
    """Agent identifiers used in Redis keys and events."""

    SAFETY = "safety"
    SCORING = "scoring"
    SENTIMENT = "sentiment"


# EVENT TYPE ENUMS


class PingType(str, Enum):
    """How the event arrived — stamped by the device or app."""

    EMERGENCY = "emergency"
    HIGH_SPEED = "high_speed"
    MEDIUM_SPEED = "medium_speed"
    BATCH = "batch"
    START_OF_TRIP = "start_of_trip"
    END_OF_TRIP = "end_of_trip"


class Source(str, Enum):
    """Who generated the event."""

    DEVICE = "telematics_device"
    DRIVER = "driver_app"
    SYSTEM = "system"
