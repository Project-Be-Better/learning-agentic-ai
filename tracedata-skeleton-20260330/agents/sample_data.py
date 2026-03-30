"""
TraceData Sample Data — Complete Event & Agent Workflow Reference

This file contains sample data for ALL event types described in the Input Data Architecture,
plus outputs from each agent component.

ORGANIZATION:
  1. INGESTION LAYER — TripEvent payloads (after Ingestion Tool processing)
     Organized by priority & event type from EVENT_MATRIX
  2. SCORING AGENT — Outputs (trip scores, explanations, fairness audits)
  3. SAFETY AGENT — Outputs (safety flags, enriched events) [Future]
  4. SENTIMENT AGENT — Outputs (wellbeing assessment) [Future]
  5. ORCHESTRATOR — Trip context and routing decisions

COVERAGE:
  - 15 event types from EVENT_MATRIX (all scenarios)
  - Priority levels: CRITICAL, HIGH, MEDIUM, LOW
  - Sources: telematics_device, driver_app
  - Agent-specific outputs and transformations

For detailed field definitions, see Input Data Architecture doc (A3).
"""

# ==============================================================================
# LAYER 1: INGESTION — TripEvent Payloads (After Ingestion Tool Processing)
# ==============================================================================

# CRITICAL PRIORITY (score=0)

DEMO_EVENT_COLLISION = {
    "event_id": "EV-EMERGENCY-T12345-001",
    "device_event_id": "DEV-COL-001",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "EMERGENCY-T12345-2026-03-07-08-44-23",
    "event_type": "collision",
    "category": "critical",
    "priority": 0,
    "timestamp": "2026-03-07T08:44:23Z",
    "offset_seconds": 2963,
    "trip_meter_km": 34.2,
    "odometer_km": 180234.2,
    "location": {"lat": 1.2863, "lon": 104.0115},
    "ping_type": "emergency",
    "source": "telematics_device",
    "is_emergency": True,
    "schema_version": "event_v1",
    "details": {
        "g_force_magnitude": 2.3,
        "confidence": 0.99,
        "airbag_triggered": True,
        "impact_direction": "front_left",
        "speed_kmh": 48,
        "injury_severity_estimate": "moderate",
    },
    "evidence": {
        "video_url": "s3://tracedata-clips/EMERGENCY-T12345-2026-03-07.mp4",
        "video_duration_seconds": 30,
        "capture_offset_seconds": -15,
        "voice_url": "s3://tracedata-voice/EMERGENCY-T12345-2026-03-07.wav",
        "voice_duration_seconds": 30,
        "sensor_dump_url": "s3://tracedata-sensors/EMERGENCY-T12345-2026-03-07.bin",
        "sensor_dump_size_bytes": 5242880,
    },
}

DEMO_EVENT_ROLLOVER = {
    "event_id": "EV-ROLLOVER-T12345-001",
    "device_event_id": "DEV-ROL-001",
    "trip_id": "TRIP-T12345-2026-03-08-14:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "EMERGENCY-T12345-2026-03-08-14-22-10",
    "event_type": "rollover",
    "category": "critical",
    "priority": 0,
    "timestamp": "2026-03-08T14:22:10Z",
    "offset_seconds": 1330,
    "trip_meter_km": 18.7,
    "odometer_km": 180419.7,
    "location": {"lat": 1.3412, "lon": 103.9021},
    "ping_type": "emergency",
    "source": "telematics_device",
    "is_emergency": True,
    "schema_version": "event_v1",
    "details": {
        "g_force_magnitude": 3.1,
        "impact_direction": "right_side",
        "roll_angle_degrees": 67,
        "confidence": 0.97,
    },
    "evidence": {
        "video_url": "s3://tracedata-clips/ROLLOVER-T12345-2026-03-08.mp4",
        "video_duration_seconds": 30,
        "capture_offset_seconds": -15,
        "voice_url": "s3://tracedata-voice/ROLLOVER-T12345-2026-03-08.wav",
        "voice_duration_seconds": 30,
        "sensor_dump_url": "s3://tracedata-sensors/ROLLOVER-T12345-2026-03-08.bin",
        "sensor_dump_size_bytes": 5242880,
    },
}

DEMO_EVENT_DRIVER_SOS = {
    "event_id": "EV-SOS-D6789-012",
    "device_event_id": "APP-SOS-012",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "SOS-D6789-2026-03-07-09-00-00",
    "event_type": "driver_sos",
    "category": "critical",
    "priority": 0,
    "timestamp": "2026-03-07T09:00:00Z",
    "offset_seconds": 3600,
    "trip_meter_km": None,
    "odometer_km": None,
    "location": {"lat": 1.2900, "lon": 104.0200},
    "ping_type": "emergency",
    "source": "driver_app",
    "is_emergency": True,
    "schema_version": "event_v1",
    "details": {
        "message": "Vehicle has broken down. Need roadside assistance.",
        "sos_type": "breakdown",
    },
    "evidence": None,
}

# HIGH PRIORITY (score=3)

DEMO_EVENT_HARSH_BRAKE = {
    "event_id": "EV-HB-T12345-002",
    "device_event_id": "DEV-HB-002",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "HIGH-T12345-2026-03-07-09-10-00",
    "event_type": "harsh_brake",
    "category": "harsh_events",
    "priority": 3,
    "timestamp": "2026-03-07T09:10:00Z",
    "offset_seconds": 4200,
    "trip_meter_km": 48.7,
    "odometer_km": 180248.7,
    "location": {"lat": 1.3000, "lon": 103.8500},
    "ping_type": "high_speed",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "g_force_x": -0.92,
        "speed_kmh": 88,
        "duration_seconds": 2,
        "confidence": 0.95,
    },
    "evidence": {
        "video_url": "s3://tracedata-clips/HIGH-T12345-2026-03-07-09-10-00.mp4",
        "video_duration_seconds": 30,
        "capture_offset_seconds": -15,
        "video_codec": "h264",
        "video_resolution": "1280x720",
    },
}

DEMO_EVENT_HARD_ACCEL = {
    "event_id": "EV-HA-T12345-003",
    "device_event_id": "DEV-HA-003",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "HIGH-T12345-2026-03-07-09-35-00",
    "event_type": "hard_accel",
    "category": "harsh_events",
    "priority": 3,
    "timestamp": "2026-03-07T09:35:00Z",
    "offset_seconds": 5700,
    "trip_meter_km": 56.1,
    "odometer_km": 180256.1,
    "location": {"lat": 1.3100, "lon": 103.8600},
    "ping_type": "high_speed",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "g_force_x": 0.82,
        "speed_kmh": 42,
        "duration_seconds": 3,
        "confidence": 0.91,
    },
    "evidence": {
        "video_url": "s3://tracedata-clips/HIGH-T12345-2026-03-07-09-35-00.mp4",
        "video_duration_seconds": 30,
        "capture_offset_seconds": -15,
        "video_codec": "h264",
        "video_resolution": "1280x720",
    },
}

DEMO_EVENT_HARSH_CORNER = {
    "event_id": "EV-HC-T12345-004",
    "device_event_id": "DEV-HC-004",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "HIGH-T12345-2026-03-07-10-05-00",
    "event_type": "harsh_corner",
    "category": "harsh_events",
    "priority": 3,
    "timestamp": "2026-03-07T10:05:00Z",
    "offset_seconds": 7500,
    "trip_meter_km": 63.4,
    "odometer_km": 180263.4,
    "location": {"lat": 1.3180, "lon": 103.8680},
    "ping_type": "high_speed",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "g_force_y": 0.87,
        "speed_kmh": 65,
        "duration_seconds": 2,
        "confidence": 0.88,
        "direction": "left",
    },
    "evidence": {
        "video_url": "s3://tracedata-clips/HIGH-T12345-2026-03-07-10-05-00.mp4",
        "video_duration_seconds": 30,
        "capture_offset_seconds": -15,
        "video_codec": "h264",
        "video_resolution": "1280x720",
    },
}

DEMO_EVENT_VEHICLE_OFFLINE = {
    "event_id": "EV-OFFLINE-T12345-005",
    "device_event_id": "DEV-OFFLINE-005",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "HIGH-T12345-2026-03-07-10-15-00",
    "event_type": "vehicle_offline",
    "category": "critical",
    "priority": 3,
    "timestamp": "2026-03-07T10:15:00Z",
    "offset_seconds": 8100,
    "trip_meter_km": 66.2,
    "odometer_km": 180266.2,
    "location": {"lat": 1.3220, "lon": 103.8720},
    "ping_type": "high_speed",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "offline_duration_seconds": 142,
        "last_known_speed_kmh": 72,
        "reconnect_timestamp": "2026-03-07T10:17:22Z",
    },
    "evidence": None,
}

DEMO_EVENT_DRIVER_DISPUTE = {
    "event_id": "EV-DISPUTE-D6789-013",
    "device_event_id": "APP-DISPUTE-013",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "DISPUTE-D6789-2026-03-07-09-30-00",
    "event_type": "driver_dispute",
    "category": "driver_feedback",
    "priority": 3,
    "timestamp": "2026-03-07T09:30:00Z",
    "offset_seconds": None,
    "trip_meter_km": None,
    "odometer_km": None,
    "location": None,
    "ping_type": "high_speed",
    "source": "driver_app",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "disputed_event_id": "DEV-HB-002",
        "disputed_event_type": "harsh_brake",
        "reason": "A car cut in front of me suddenly. I had to brake hard to avoid a collision.",
        "supporting_note": "Check dashcam footage at 09:10 on AYE",
    },
    "evidence": None,
}

# MEDIUM PRIORITY (score=6)

DEMO_EVENT_SPEEDING = {
    "event_id": "EV-SPD-T12345-006",
    "device_event_id": "DEV-SPD-006",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "MEDIUM-T12345-2026-03-07-10-00-00",
    "event_type": "speeding",
    "category": "speed_compliance",
    "priority": 6,
    "timestamp": "2026-03-07T10:00:00Z",
    "offset_seconds": 7200,
    "trip_meter_km": 62.4,
    "odometer_km": 180262.4,
    "location": {"lat": 1.3200, "lon": 103.8700},
    "ping_type": "medium_speed",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "speed_kmh": 112,
        "speed_limit_kmh": 90,
        "duration_seconds": 45,
        "confidence": 0.97,
    },
    "evidence": None,
}

DEMO_EVENT_DRIVER_FEEDBACK = {
    "event_id": "EV-FB-D6789-014",
    "device_event_id": "APP-FB-014",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "FEEDBACK-D6789-2026-03-07-11-00-00",
    "event_type": "driver_feedback",
    "category": "driver_feedback",
    "priority": 6,
    "timestamp": "2026-03-07T11:00:00Z",
    "offset_seconds": None,
    "trip_meter_km": None,
    "odometer_km": None,
    "location": None,
    "ping_type": "medium_speed",
    "source": "driver_app",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "trip_rating": 4,
        "message": "Long trip today but manageable. Traffic on AYE was bad around 9am.",
        "fatigue_self_report": "mild",
    },
    "evidence": None,
}

# LOW PRIORITY (score=9)

DEMO_EVENT_EXCESSIVE_IDLE = {
    "event_id": "EV-IDLE-T12345-007",
    "device_event_id": "DEV-IDLE-007",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "BATCH-T12345-2026-03-07-10-10-00",
    "event_type": "excessive_idle",
    "category": "idle_fuel",
    "priority": 9,
    "timestamp": "2026-03-07T10:08:00Z",
    "offset_seconds": 7680,
    "trip_meter_km": 64.0,
    "odometer_km": 180264.0,
    "location": {"lat": 1.3210, "lon": 103.8710},
    "ping_type": "batch",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "idle_duration_seconds": 342,
        "fuel_wasted_estimate_litres": 0.046,
        "engine_rpm_during_idle": 820,
    },
    "evidence": None,
}

DEMO_EVENT_SMOOTHNESS_LOG = {
    "event_id": "EV-SMOOTH-T12345-008",
    "device_event_id": "DEV-SMOOTH-008",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "BATCH-T12345-2026-03-07-10-10-00",
    "event_type": "smoothness_log",
    "category": "normal_operation",
    "priority": 9,
    "timestamp": "2026-03-07T10:10:00Z",
    "offset_seconds": 7800,
    "trip_meter_km": 68.1,
    "odometer_km": 180268.1,
    "location": {"lat": 1.3250, "lon": 103.8750},
    "ping_type": "batch",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "sample_count": 600,
        "window_seconds": 600,
        "speed": {
            "mean_kmh": 72.3,
            "std_dev": 8.1,
            "max_kmh": 94.0,
            "variance": 65.6,
        },
        "longitudinal": {
            "mean_accel_g": 0.04,
            "std_dev": 0.12,
            "max_decel_g": -0.31,
            "harsh_brake_count": 0,
            "harsh_accel_count": 0,
        },
        "lateral": {
            "mean_lateral_g": 0.02,
            "max_lateral_g": 0.18,
            "harsh_corner_count": 0,
        },
        "jerk": {
            "mean": 0.008,
            "max": 0.041,
            "std_dev": 0.006,
        },
        "engine": {
            "mean_rpm": 1820,
            "max_rpm": 2340,
            "idle_seconds": 45,
            "idle_events": 1,
            "longest_idle_seconds": 38,
            "over_rev_count": 0,
            "over_rev_seconds": 0,
        },
        "incident_event_ids": ["DEV-HB-002", "DEV-SPD-006"],
        "raw_log_url": "s3://tracedata-sensors/T12345-batch-20260307-1010.bin",
    },
    "evidence": None,
}

DEMO_EVENT_NORMAL_OPERATION = {
    "event_id": "EV-SAFE-T12345-009",
    "device_event_id": "DEV-SAFE-009",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "BATCH-T12345-2026-03-07-10-10-00",
    "event_type": "normal_operation",
    "category": "normal_operation",
    "priority": 9,
    "timestamp": "2026-03-07T10:04:00Z",
    "offset_seconds": 7440,
    "trip_meter_km": 65.3,
    "odometer_km": 180265.3,
    "location": {"lat": 1.3230, "lon": 103.8730},
    "ping_type": "batch",
    "source": "telematics_device",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "checkpoint_number": 18,
        "distance_km": 0.7,
        "violations_in_period": 0,
    },
    "evidence": None,
}

DEMO_EVENT_START_OF_TRIP = {
    "event_id": "EV-SOT-T12345-010",
    "device_event_id": "APP-SOT-010",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "SOT-T12345-2026-03-07-08-00-00",
    "event_type": "start_of_trip",
    "category": "trip_lifecycle",
    "priority": 9,
    "timestamp": "2026-03-07T08:00:00Z",
    "offset_seconds": 0,
    "trip_meter_km": 0.0,
    "odometer_km": 180200.0,
    "location": {"lat": 1.3456, "lon": 103.8301},
    "ping_type": "start_of_trip",
    "source": "driver_app",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "odometer_km": 180200.0,
        "fuel_level_litres": 45,
        "vehicle_status": "ready",
        "driver_confirmation": True,
        "intended_destination": "Port of Singapore",
        "estimated_distance_km": 78,
    },
    "evidence": None,
}

DEMO_EVENT_END_OF_TRIP = {
    "event_id": "EV-EOT-T12345-011",
    "device_event_id": "APP-EOT-011",
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "batch_id": "EOT-T12345-2026-03-07-10-45-32",
    "event_type": "end_of_trip",
    "category": "trip_lifecycle",
    "priority": 9,
    "timestamp": "2026-03-07T10:45:32Z",
    "offset_seconds": 9932,
    "trip_meter_km": 78.3,
    "odometer_km": 180278.3,
    "location": {"lat": 1.2900, "lon": 103.8500},
    "ping_type": "end_of_trip",
    "source": "driver_app",
    "is_emergency": False,
    "schema_version": "event_v1",
    "details": {
        "duration_minutes": 165,
        "distance_km": 78.3,
        "harsh_events_total": 8,
        "speeding_events": 2,
        "safe_operation_checkpoints": 28,
        "total_checkpoints": 38,
        "safety_percentage": 73.7,
        "fuel_consumed_litres": 9.8,
        "avg_speed_kmh": 28.5,
        "max_speed_kmh": 112,
    },
    "evidence": None,
}

# ==============================================================================
# LAYER 2: ORCHESTRATOR — Trip Context
# ==============================================================================

DEMO_TRIP_CONTEXT = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "driver_age": 28,
    "experience_level": "medium",
    "historical_avg_score": 71.2,
    "peer_group_avg": 68.4,
    "duration_minutes": 165,
    "distance_km": 78.3,
    "window_count": 16,
}

# ==============================================================================
# LAYER 3: SCORING AGENT — Outputs
# ==============================================================================

DEMO_SCORING_AGENT_TRIP_SCORE = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "behaviour_score": 74.3,
    "smoothness_score": 74.3,
    "harsh_event_count": 4,
    "smoothness_windows": 16,
    "model_version": "xgb_v1.2",
    "fairness_passed": True,
    "disparate_impact": 0.98,
    "scored_at": "2026-03-07T10:45:32Z",
}

DEMO_SCORING_AGENT_SHAP_EXPLANATION = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "top_features": [
        {
            "feature": "jerk_mean",
            "value": 0.015,
            "shap_value": 0.25,
            "contribution": "positive",
            "interpretation": "Smooth acceleration and braking",
        },
        {
            "feature": "speed_std_dev",
            "value": 12.1,
            "shap_value": 0.18,
            "contribution": "positive",
            "interpretation": "Consistent speed control",
        },
        {
            "feature": "mean_lateral_g",
            "value": 0.027,
            "shap_value": 0.12,
            "contribution": "positive",
            "interpretation": "Smooth cornering technique",
        },
        {
            "feature": "idle_ratio",
            "value": 0.14,
            "shap_value": -0.08,
            "contribution": "negative",
            "interpretation": "Excessive idle time",
        },
    ],
    "base_score": 50.0,
    "final_score": 74.3,
    "narrative": (
        "The driver's smooth acceleration and braking (low jerk, +0.25) "
        "combined with consistent speed control (+0.18) are the main drivers "
        "of the high score. Smooth cornering (+0.12) also helps. "
        "Excessive idle time (-0.08) slightly reduces the score."
    ),
}

DEMO_SCORING_AGENT_FAIRNESS_AUDIT = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "protected_attribute": "driver_age",
    "metric_name": "disparate_impact",
    "demographic_parity": "PASS",
    "equalized_odds": "PASS",
    "disparate_impact": 0.98,
    "bias_score": 0.02,
    "bias_detected": False,
    "is_edge_case": False,
    "recommendation": (
        "Score is fair across demographic groups (age, experience level). "
        "No evidence of systematic bias. Driver (age 28, medium experience) "
        "scored consistently with peers in same demographic group."
    ),
}

# ==============================================================================
# EVENT COLLECTIONS BY PRIORITY & AGENT
# ==============================================================================

ALL_CRITICAL_EVENTS = [
    DEMO_EVENT_COLLISION,
    DEMO_EVENT_ROLLOVER,
    DEMO_EVENT_DRIVER_SOS,
]

ALL_HIGH_PRIORITY_EVENTS = [
    DEMO_EVENT_HARSH_BRAKE,
    DEMO_EVENT_HARD_ACCEL,
    DEMO_EVENT_HARSH_CORNER,
    DEMO_EVENT_VEHICLE_OFFLINE,
    DEMO_EVENT_DRIVER_DISPUTE,
]

ALL_MEDIUM_PRIORITY_EVENTS = [
    DEMO_EVENT_SPEEDING,
    DEMO_EVENT_DRIVER_FEEDBACK,
]

ALL_LOW_PRIORITY_EVENTS = [
    DEMO_EVENT_EXCESSIVE_IDLE,
    DEMO_EVENT_SMOOTHNESS_LOG,
    DEMO_EVENT_NORMAL_OPERATION,
    DEMO_EVENT_START_OF_TRIP,
    DEMO_EVENT_END_OF_TRIP,
]

ALL_TELEMATICS_EVENTS = (
    ALL_CRITICAL_EVENTS
    + ALL_HIGH_PRIORITY_EVENTS
    + ALL_MEDIUM_PRIORITY_EVENTS
    + ALL_LOW_PRIORITY_EVENTS
)

SAFETY_AGENT_EVENTS = [
    DEMO_EVENT_COLLISION,
    DEMO_EVENT_ROLLOVER,
    DEMO_EVENT_HARSH_BRAKE,
    DEMO_EVENT_HARD_ACCEL,
    DEMO_EVENT_HARSH_CORNER,
    DEMO_EVENT_VEHICLE_OFFLINE,
    DEMO_EVENT_SPEEDING,
]

SCORING_AGENT_EVENTS = [
    DEMO_EVENT_SMOOTHNESS_LOG,
    DEMO_EVENT_HARSH_BRAKE,
    DEMO_EVENT_HARSH_CORNER,
    DEMO_EVENT_HARD_ACCEL,
]

SENTIMENT_AGENT_EVENTS = [
    DEMO_EVENT_DRIVER_FEEDBACK,
    DEMO_EVENT_DRIVER_DISPUTE,
]

ORCHESTRATOR_EVENTS = [
    DEMO_EVENT_START_OF_TRIP,
    DEMO_EVENT_END_OF_TRIP,
]
