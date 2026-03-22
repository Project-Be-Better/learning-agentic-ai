from pydantic import BaseModel, ConfigDict


class EventConfig(BaseModel):
    """Configuration for event routing and ML scoring."""

    model_config = ConfigDict(frozen=True)

    category: str
    priority: str
    ml_weight: float | None = None


# EVENT MATRIX
# Single source of truth for event routing and ML weights.
# Ingestion tool validates all events against this.

EVENT_MATRIX: dict[str, EventConfig] = {
    # DEVICE EVENTS
    "collision": EventConfig("critical", "critical", 1.0),
    "rollover": EventConfig("critical", "critical", 1.0),
    "vehicle_offline": EventConfig("critical", "high", 0.3),
    "harsh_brake": EventConfig("harsh_events", "high", 0.7),
    "hard_accel": EventConfig("harsh_events", "high", 0.7),
    "harsh_corner": EventConfig("harsh_events", "high", 0.6),
    "speeding": EventConfig("speed_compliance", "medium", 0.5),
    "excessive_idle": EventConfig("idle_fuel", "low", 0.2),
    "normal_operation": EventConfig("normal_operation", "low", 0.0),
    "start_of_trip": EventConfig("trip_lifecycle", "low", None),
    "end_of_trip": EventConfig("trip_lifecycle", "low", None),
    # DRIVER GENERATED EVENTS
    "driver_sos": EventConfig("critical", "critical", None),
    "driver_dispute": EventConfig("driver_feedback", "high", None),
    "driver_complaint": EventConfig("driver_feedback", "high", None),
    "driver_feedback": EventConfig("driver_feedback", "medium", None),
    "driver_comment": EventConfig("driver_feedback", "low", None),
}
