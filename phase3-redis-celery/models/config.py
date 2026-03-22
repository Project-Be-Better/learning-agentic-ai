from pydantic import BaseModel, ConfigDict


class EventConfig(BaseModel):
    """
    Configuration for a single event type.
    Frozen — values cannot change at runtime.

    ml_weight:
      positive  → penalty contribution to driver score
      negative  → reward bonus (e.g. smoothness_log = -0.2)
      None      → not scored (driver feedback, lifecycle events)
    """

    model_config = ConfigDict(frozen=True)

    category: str
    priority: str
    ml_weight: float | None = None


# ── EVENT MATRIX ─────────────────────────────────────────
# Single source of truth for event routing and ML weights.
# Ingestion Tool validates all incoming events against this.
# Orchestrator reads category to decide agent dispatch.
# Scoring Agent reads ml_weight in Sprint 3.

EVENT_MATRIX: dict[str, EventConfig] = {
    # DEVICE EVENTS — safety critical
    "collision": EventConfig(category="critical", priority="critical", ml_weight=1.0),
    "rollover": EventConfig(category="critical", priority="critical", ml_weight=1.0),
    "vehicle_offline": EventConfig(category="critical", priority="high", ml_weight=0.3),
    # DEVICE EVENTS — harsh driving
    "harsh_brake": EventConfig(category="harsh_events", priority="high", ml_weight=0.7),
    "hard_accel": EventConfig(category="harsh_events", priority="high", ml_weight=0.7),
    "harsh_corner": EventConfig(
        category="harsh_events", priority="high", ml_weight=0.6
    ),
    # DEVICE EVENTS — compliance
    "speeding": EventConfig(
        category="speed_compliance", priority="medium", ml_weight=0.5
    ),
    # DEVICE EVENTS — efficiency
    "excessive_idle": EventConfig(category="idle_fuel", priority="low", ml_weight=0.2),
    # DEVICE EVENTS — positive behaviour
    # smoothness_log carries negative ml_weight — reward bonus not penalty
    "smoothness_log": EventConfig(
        category="normal_operation", priority="low", ml_weight=-0.2
    ),
    "normal_operation": EventConfig(
        category="normal_operation", priority="low", ml_weight=0.0
    ),
    # DEVICE EVENTS — trip lifecycle
    "start_of_trip": EventConfig(
        category="trip_lifecycle", priority="low", ml_weight=None
    ),
    "end_of_trip": EventConfig(
        category="trip_lifecycle", priority="low", ml_weight=None
    ),
    # DRIVER GENERATED EVENTS
    # ml_weight=None — driver feedback does not feed XGBoost score
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


# ── THRESHOLDS ───────────────────────────────────────────
# Externalised operational thresholds for device events.
# Ingestion Tool cross-checks event details against these.
# Configurable without firmware updates or code redeployment.

THRESHOLDS: dict[str, dict] = {
    "idle": {
        # below acceptable  → no flag, normal operation
        # warning zone      → flagged for review, no event fired
        # above excessive   → excessive_idle event triggered
        "acceptable_seconds": 120,
        "warning_seconds": 300,
        "excessive_seconds": 300,
    },
    "rpm": {
        # normal cruising range for trucks
        # over_rev must be sustained for duration to count
        "normal_max": 1800,
        "acceptable_max": 2500,
        "over_rev_threshold": 2500,
        "over_rev_duration_seconds": 5,
    },
    "acceleration": {
        # G-force thresholds for harsh event detection
        "harsh_brake_g": -0.7,  # deceleration
        "harsh_accel_g": 0.75,  # acceleration
        "harsh_corner_g": 0.8,  # lateral
    },
    "jerk": {
        # rate of change of acceleration (m/s³)
        # below smooth_threshold → counts as a smooth second
        "smooth_threshold": 0.05,
    },
    "speed": {
        # sustained over limit triggers speeding event
        "speeding_duration_seconds": 30,
    },
}


# ── SMOOTHNESS LOG DETAILS REFERENCE ─────────────────────
# Reference schema for the details block of smoothness_log events.
# details is a free dict in TelemetryEvent — this documents
# the expected structure for Scoring Agent consumption.
#
# Device computes all stats from 600 1Hz samples per 10-min window.
# Scoring Agent applies XGBoost formula using these stats.
# Raw 600-point arrays are uploaded to S3 — not included here.

SMOOTHNESS_LOG_DETAILS: dict[str, str] = {
    "sample_count": "int   — number of 1Hz samples in window (typically 600)",
    "window_seconds": "int   — duration of sampling window in seconds",
    "speed": {
        "mean_kmh": "float — mean speed over window",
        "std_dev": "float — speed consistency (lower = smoother)",
        "max_kmh": "float — peak speed in window",
        "variance": "float — speed variance",
    },
    "longitudinal": {
        "mean_accel_g": "float — mean forward/braking G-force",
        "std_dev": "float — consistency of acceleration pattern",
        "max_decel_g": "float — hardest braking event in window",
        "harsh_brake_count": "int   — times threshold exceeded",
        "harsh_accel_count": "int   — times threshold exceeded",
    },
    "lateral": {
        "mean_lateral_g": "float — mean cornering G-force",
        "max_lateral_g": "float — hardest corner in window",
        "harsh_corner_count": "int   — times threshold exceeded",
    },
    "jerk": {
        "mean": "float — mean rate of acceleration change (m/s³)",
        "max": "float — worst sudden movement in window",
        "std_dev": "float — jerk consistency (lower = smoother)",
    },
    "engine": {
        "mean_rpm": "float — mean engine RPM over window",
        "max_rpm": "float — peak RPM in window",
        "idle_seconds": "int   — total idle time in window",
        "idle_events": "int   — number of distinct idle periods",
        "longest_idle_seconds": "int   — longest single idle period",
        "over_rev_count": "int   — times RPM exceeded threshold",
        "over_rev_seconds": "int   — total seconds over RPM threshold",
    },
    "incident_event_ids": "list[str] — device_event_ids of events in this window",
    "raw_log_url": "str       — S3 link to compressed 600-point binary",
}
