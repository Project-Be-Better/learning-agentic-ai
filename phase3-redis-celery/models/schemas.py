from pydantic import BaseModel
from .enums import Priority, AgentName, Source, PingType


# ── RAW DEVICE PAYLOADS ──────────────────────────────────


class Location(BaseModel):
    """GPS coordinates of the event."""

    lat: float
    lon: float


class TelemetryEvent(BaseModel):
    """
    Generic event schema for all telematics device events.
    details field is flexible — shape depends on event_type.

    Spatio-temporal anchor fields:
      offset_seconds  → when in the trip (time)
      trip_meter_km   → where in the trip (distance)
      odometer_km     → absolute vehicle lifetime distance
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

    # spatio-temporal anchor — present on all device pings
    # None for driver app events (app does not have device fields)
    offset_seconds: int | None = None
    trip_meter_km: float | None = None
    odometer_km: float | None = None

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
    Full raw payload arriving from the telematics device or driver app.
    This is what gets written to the Redis telemetry buffer.
    ping_type and source are stamped by the sender.
    """

    batch_id: str
    ping_type: PingType
    source: Source = Source.DEVICE
    is_emergency: bool = False
    event: TelemetryEvent
    evidence: Evidence | None = None


# ── PROCESSED EVENT ──────────────────────────────────────


class TripEvent(BaseModel):
    """
    Cleaned, flat event produced by the Ingestion Tool.
    This is what the Orchestrator and agents work with.

    Preserves spatio-temporal anchor from TelemetryEvent
    for distance normalisation in fairness scoring.
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
    ping_type: PingType  # routing decisions
    source: Source  # audit trail

    # spatio-temporal anchor — preserved from TelemetryEvent
    offset_seconds: int | None = None
    trip_meter_km: float | None = None
    odometer_km: float | None = None

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


class CompletionEvent(BaseModel):
    """
    Published to Redis Pub/Sub when an agent finishes.
    Orchestrator listens for these to advance the workflow.
    """

    trip_id: str
    agent: AgentName
    status: str
    final: bool = False
