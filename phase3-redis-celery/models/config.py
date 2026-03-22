# ── EVENT MATRIX ────────────────────────────────────────
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
