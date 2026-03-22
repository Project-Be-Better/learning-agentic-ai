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
    "collision": EventConfig(category="critical", priority="critical", ml_weight=1.0),
    "rollover": EventConfig(category="critical", priority="critical", ml_weight=1.0),
    "vehicle_offline": EventConfig(category="critical", priority="high", ml_weight=0.3),
    "harsh_brake": EventConfig(category="harsh_events", priority="high", ml_weight=0.7),
    "hard_accel": EventConfig(category="harsh_events", priority="high", ml_weight=0.7),
    "harsh_corner": EventConfig(
        category="harsh_events", priority="high", ml_weight=0.6
    ),
    "speeding": EventConfig(
        category="speed_compliance", priority="medium", ml_weight=0.5
    ),
    "excessive_idle": EventConfig(category="idle_fuel", priority="low", ml_weight=0.2),
    "normal_operation": EventConfig(
        category="normal_operation", priority="low", ml_weight=0.0
    ),
    "start_of_trip": EventConfig(
        category="trip_lifecycle", priority="low", ml_weight=None
    ),
    "end_of_trip": EventConfig(
        category="trip_lifecycle", priority="low", ml_weight=None
    ),
    # DRIVER GENERATED EVENTS
    "driver_sos": EventConfig(category="critical", priority="critical", ml_weight=None),
    "driver_dispute": EventConfig(
        category="driver_feedback", priority="high", ml_weight=None
    ),
    "driver_complaint": EventConfig(
        category="driver_feedback", priority="high", ml_weight=None
    ),
    "driver_feedback": EventConfig(
        category="driver_feedback", priority="medium", ml_weight=None
    ),
    "driver_comment": EventConfig(
        category="driver_feedback", priority="low", ml_weight=None
    ),
}
