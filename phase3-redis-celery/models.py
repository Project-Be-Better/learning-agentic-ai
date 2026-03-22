from enum import IntEnum, Enum
from pydantic import BaseModel


# ── ENUMS ───────────────────────────────────────────────


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


# ── RAW DEVICE PAYLOAD ───────────────────────────────────


class Location(BaseModel):
    """GPS coordinates of the event."""

    lat: float
    lon: float


class TelemetryEvent(BaseModel):
    """
    Generic event schema for all telematics device events.
    details field is flexible — shape depends on event_type.
    """

    event_id: str
    device_event_id: str
    trip_id: str
    driver_id: str
    truck_id: str
    event_type: str
    category: str
    priority: str
    timestamp: str
    schema_version: str = "event_v1"
    offset_seconds: int | None = None
    location: Location | None = None
    details: dict = {}


class Evidence(BaseModel):
    """
    Optional evidence attached to an event.
    Populated when device uploads media to S3.
    """

    video_url: str | None = None
    video_duration_seconds: int | None = None
    voice_url: str | None = None
    voice_duration_seconds: int | None = None
    sensor_dump_url: str | None = None
    sensor_dump_size_bytes: int | None = None


class TelemetryPacket(BaseModel):
    """
    Full raw payload arriving from the telematics device.
    This is what gets written to the Redis telemetry buffer.
    """

    batch_id: str
    source: str = "telematics_device"
    is_emergency: bool = False
    event: TelemetryEvent
    evidence: Evidence | None = None


# ── PROCESSED EVENT ──────────────────────────────────────


class TripEvent(BaseModel):
    """
    Cleaned, flat event produced by the Ingestion Tool.
    This is what the Orchestrator and agents work with.
    """

    batch_id: str
    trip_id: str
    driver_id: str
    truck_id: str
    timestamp: str
    event_type: str
    category: str
    priority: Priority
    is_emergency: bool
    location: Location | None = None
    details: dict = {}
    evidence: Evidence | None = None


# ── TRIP CONTEXT ─────────────────────────────────────────


class TripContext(BaseModel):
    """
    Written to Redis by Orchestrator at job start.
    Every agent hydrates from this on task pickup.
    """

    trip_id: str
    driver_id: str
    truck_id: str
    priority: Priority
    event: TripEvent


# ── AGENT RESULTS ────────────────────────────────────────


class SafetyResult(BaseModel):
    """Output contract for the Safety Agent."""

    trip_id: str
    agent: AgentName
    score: float
    flags: list[str]
    requires_human_review: bool


# ── COMPLETION EVENT ─────────────────────────────────────


class CompletionEvent(BaseModel):
    """
    Published to Redis Pub/Sub when an agent finishes.
    Orchestrator listens for these to advance the workflow.
    """

    trip_id: str
    agent: AgentName
    status: str
    final: bool = False


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


# ── ADD EVENT MATRIX ─────────────────────────────────────
# Single source of truth for event routing and ML weights.
# Ingestion tool validates all events against this.

EVENT_MATRIX: dict[str, dict] = {
    # ── DEVICE EVENTS ────────────────────────────────────
    "collision": {"category": "critical", "priority": "critical", "ml_weight": 1.0},
    "rollover": {"category": "critical", "priority": "critical", "ml_weight": 1.0},
    "vehicle_offline": {"category": "critical", "priority": "high", "ml_weight": 0.3},
    "harsh_brake": {"category": "harsh_events", "priority": "high", "ml_weight": 0.7},
    "hard_accel": {"category": "harsh_events", "priority": "high", "ml_weight": 0.7},
    "harsh_corner": {"category": "harsh_events", "priority": "high", "ml_weight": 0.6},
    "speeding": {
        "category": "speed_compliance",
        "priority": "medium",
        "ml_weight": 0.5,
    },
    "excessive_idle": {"category": "idle_fuel", "priority": "low", "ml_weight": 0.2},
    "normal_operation": {
        "category": "normal_operation",
        "priority": "low",
        "ml_weight": 0.0,
    },
    "start_of_trip": {
        "category": "trip_lifecycle",
        "priority": "low",
        "ml_weight": None,
    },
    "end_of_trip": {"category": "trip_lifecycle", "priority": "low", "ml_weight": None},
    # ── DRIVER GENERATED EVENTS ──────────────────────────
    "driver_sos": {"category": "critical", "priority": "critical", "ml_weight": None},
    "driver_dispute": {
        "category": "driver_feedback",
        "priority": "high",
        "ml_weight": None,
    },
    "driver_complaint": {
        "category": "driver_feedback",
        "priority": "high",
        "ml_weight": None,
    },
    "driver_feedback": {
        "category": "driver_feedback",
        "priority": "medium",
        "ml_weight": None,
    },
    "driver_comment": {
        "category": "driver_feedback",
        "priority": "low",
        "ml_weight": None,
    },
}
