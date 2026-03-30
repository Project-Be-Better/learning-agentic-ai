"""
Scoring Agent Tools — DEMO VERSION with Composite Score + Explain + Audit

COMPREHENSIVE DATA CONTRACTS:
─────────────────────────────────────────────────────────────────────────────

This module uses demo data from /tracedata/common/sample_data.py covering
ALL 15 EVENT TYPES from the INPUT DATA ARCHITECTURE:

CRITICAL (priority=0):
  - collision, rollover, driver_sos

HIGH (priority=3):
  - harsh_brake, hard_accel, harsh_corner, vehicle_offline, driver_dispute

MEDIUM (priority=6):
  - speeding, driver_feedback

LOW (priority=9):
  - excessive_idle, smoothness_log, normal_operation, start_of_trip, end_of_trip

ORCHESTRATOR LAYER:
  - DEMO_TRIP_CONTEXT (trip metadata + demographics)

SCORING AGENT OUTPUTS:
  - DEMO_SCORING_AGENT_TRIP_SCORE
  - DEMO_SCORING_AGENT_SHAP_EXPLANATION
  - DEMO_SCORING_AGENT_FAIRNESS_AUDIT

INPUT LAYER (Tools 1-3):
  1. get_trip_context(trip_id)
     → {trip_id, driver_id, truck_id, distance_km, duration_minutes,
         driver_age, experience_level, historical_avg_score, peer_group_avg}

  2. get_smoothness_logs(trip_id)
     → {window_count, windows: [{window_index, trip_meter_km, jerk_mean,
         jerk_max, jerk_std_dev, speed_mean_kmh, speed_std_dev,
         mean_lateral_g, max_lateral_g, mean_rpm, idle_seconds}, ...]}

  3. get_harsh_events(trip_id)
     → {event_count, events: [{event_id, event_type, trip_meter_km,
         peak_force_g, speed_at_event_kmh}, ...]}

FEATURE EXTRACTION LAYER (Tool 4):
  4. extract_scoring_features(smoothness_logs, harsh_events)
     → aggregated features for XGBoost

SCORING LAYER (Tool 5):
  5. score_and_audit_trip(trip_id, smoothness_features, demographics)
     → {behaviour_score, shap_explanation, fairness_audit}

─────────────────────────────────────────────────────────────────────────────
"""

import json
from typing import Any

from langchain_core.tools import tool

# Import comprehensive sample data from project root
# Covers all 15 event types + agent outputs
from ..sample_data import (
    # INGESTION LAYER — All event types
    DEMO_EVENT_HARSH_BRAKE,
    DEMO_EVENT_SMOOTHNESS_LOG,
    DEMO_SCORING_AGENT_FAIRNESS_AUDIT,
    DEMO_SCORING_AGENT_SHAP_EXPLANATION,
    # SCORING AGENT OUTPUTS
    DEMO_SCORING_AGENT_TRIP_SCORE,
    DEMO_TRIP_CONTEXT,
)

# ==============================================================================
# TOOL 1: Get Trip Context
# ==============================================================================


@tool
def get_trip_context(trip_id: str, redis_client: Any = None) -> str:
    """
    Get trip context from Redis.

    DEMO VERSION: Returns hardcoded data.
    PROD VERSION: Reads from redis_client.get(f"trip:{trip_id}:context")

    Returns: TripContext JSON with driver_id, truck_id, demographics,
             historical_avg_score, peer_group_avg, etc.

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    return json.dumps(DEMO_TRIP_CONTEXT)


# ==============================================================================
# TOOL 2: Get Smoothness Logs
# ==============================================================================


@tool
def get_smoothness_logs(trip_id: str, redis_client: Any = None) -> str:
    """
    Get smoothness windows from Redis.

    DEMO VERSION: Extracts from DEMO_EVENT_SMOOTHNESS_LOG.
    PROD VERSION: Reads from redis_client.lrange(f"trip:{trip_id}:smoothness_logs", 0, -1)

    Returns: Array of 6-16 smoothness windows with jerk, speed, RPM, idle metrics

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    # DEMO: Extract smoothness window details from event
    # In production, these would be multiple windows from Redis
    smoothness_event = DEMO_EVENT_SMOOTHNESS_LOG
    window_data = {
        "window_index": 0,
        "trip_meter_km": smoothness_event["trip_meter_km"],
        **smoothness_event["details"],  # Contains speed, jerk, lateral, engine stats
    }

    return json.dumps({"window_count": 1, "windows": [window_data]})


# ==============================================================================
# TOOL 3: Get Harsh Events
# ==============================================================================


@tool
def get_harsh_events(trip_id: str, redis_client: Any = None) -> str:
    """
    Get harsh events (braking, acceleration, cornering) from Redis.

    DEMO VERSION: Extracts from DEMO_EVENT_HARSH_BRAKE and similar events.
    PROD VERSION: Reads from redis_client.lrange(f"trip:{trip_id}:harsh_events", 0, -1)

    Returns: Array of harsh events with event_type, peak_force_g, speed_at_event_kmh

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    # DEMO: Collect harsh events from ingestion layer
    # In production, these would be multiple events from Redis
    harsh_events = [
        {
            "event_id": DEMO_EVENT_HARSH_BRAKE["event_id"],
            "event_type": DEMO_EVENT_HARSH_BRAKE["event_type"],
            "trip_meter_km": DEMO_EVENT_HARSH_BRAKE["trip_meter_km"],
            "peak_force_g": abs(DEMO_EVENT_HARSH_BRAKE["details"]["g_force_x"]),
            "speed_at_event_kmh": DEMO_EVENT_HARSH_BRAKE["details"]["speed_kmh"],
        },
    ]

    return json.dumps({"event_count": len(harsh_events), "events": harsh_events})


# ==============================================================================
# TOOL 4: Extract Scoring Features (Aggregation & Calculation)
# ==============================================================================


@tool
def extract_scoring_features(
    smoothness_logs_json: str,
    harsh_events_json: str,
    trip_duration_minutes: float,
    trip_distance_km: float,
) -> str:
    """
    Extract and aggregate features from raw smoothness logs and harsh events.

    INPUT CONTRACT:
      smoothness_logs_json: JSON string from get_smoothness_logs()
                            Must contain: {window_count, windows: [{...}, ...]}
      harsh_events_json: JSON string from get_harsh_events()
                        Must contain: {event_count, events: [{...}, ...]}
      trip_duration_minutes: From trip context
      trip_distance_km: From trip context

    OUTPUT CONTRACT:
      {
        "smoothness_features": {
          "jerk_mean_avg": float,           ← Average jerk across all windows
          "jerk_max_peak": float,           ← Peak jerk in any window
          "speed_std_avg": float,           ← Average speed std deviation
          "mean_lateral_g_avg": float,      ← Average lateral g
          "max_lateral_g_peak": float,      ← Peak lateral g
          "mean_rpm_avg": float,            ← Average RPM
          "idle_ratio": float,              ← Total idle time / total trip time
          "harsh_brake_count": int,         ← Number of harsh brake events
          "harsh_brake_rate_per_100km": float ← Events per 100 km traveled
        },
        "raw_smoothness_logs": {...},       ← Pass through
        "raw_harsh_events": {...}           ← Pass through
      }

    DEMO: Calculates from hardcoded data
    PROD: Calculates from actual Redis data
    """
    try:
        smoothness_data = json.loads(smoothness_logs_json)
        harsh_data = json.loads(harsh_events_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    windows = smoothness_data.get("windows", [])
    events = harsh_data.get("events", [])

    # Calculate smoothness feature aggregates
    if windows:
        jerk_means = [w.get("jerk_mean", 0) for w in windows]
        jerk_maxes = [w.get("jerk_max", 0) for w in windows]
        speed_stds = [w.get("speed_std_dev", 0) for w in windows]
        lateral_gs = [w.get("mean_lateral_g", 0) for w in windows]
        lateral_g_peaks = [w.get("max_lateral_g", 0) for w in windows]
        rpms = [w.get("mean_rpm", 0) for w in windows]
        idle_seconds = [w.get("idle_seconds", 0) for w in windows]

        jerk_mean_avg = sum(jerk_means) / len(jerk_means)
        jerk_max_peak = max(jerk_maxes) if jerk_maxes else 0
        speed_std_avg = sum(speed_stds) / len(speed_stds)
        mean_lateral_g_avg = sum(lateral_gs) / len(lateral_gs)
        max_lateral_g_peak = max(lateral_g_peaks) if lateral_g_peaks else 0
        mean_rpm_avg = sum(rpms) / len(rpms)

        total_idle_seconds = sum(idle_seconds)
        trip_duration_seconds = trip_duration_minutes * 60
        idle_ratio = (
            total_idle_seconds / trip_duration_seconds
            if trip_duration_seconds > 0
            else 0
        )
    else:
        jerk_mean_avg = speed_std_avg = mean_lateral_g_avg = max_lateral_g_peak = (
            mean_rpm_avg
        ) = 0.0
        jerk_max_peak = 0.0
        idle_ratio = 0.0

    # Count harsh events
    harsh_brake_count = sum(1 for e in events if e.get("event_type") == "harsh_brake")
    harsh_brake_rate_per_100km = (
        (harsh_brake_count / trip_distance_km * 100) if trip_distance_km > 0 else 0
    )

    return json.dumps(
        {
            "smoothness_features": {
                "jerk_mean_avg": round(jerk_mean_avg, 4),
                "jerk_max_peak": round(jerk_max_peak, 4),
                "speed_std_avg": round(speed_std_avg, 2),
                "mean_lateral_g_avg": round(mean_lateral_g_avg, 3),
                "max_lateral_g_peak": round(max_lateral_g_peak, 3),
                "mean_rpm_avg": round(mean_rpm_avg, 0),
                "idle_ratio": round(idle_ratio, 3),
                "harsh_brake_count": harsh_brake_count,
                "harsh_brake_rate_per_100km": round(harsh_brake_rate_per_100km, 2),
            },
            "raw_smoothness_logs": smoothness_data,
            "raw_harsh_events": harsh_data,
        }
    )


# ==============================================================================
# TOOL 5: COMPOSITE TOOL — Score + Explain (SHAP) + Audit (Fairness)
# ==============================================================================


@tool
def score_and_audit_trip(
    trip_id: str,
    smoothness_features: str,
    demographics: str,
    xai_engine: Any = None,
    fairness_auditor: Any = None,
) -> str:
    """
    Complete scoring operation: Score the trip + Explain with SHAP + Audit for fairness.

    COMPOSITE TOOL: This is the main operation that always runs together.

    INPUT CONTRACT (Strict):
      trip_id: str
               Trip identifier

      smoothness_features: JSON string from extract_scoring_features()
                          Must contain:
                          {
                            "smoothness_features": {
                              "jerk_mean_avg": float,
                              "jerk_max_peak": float,
                              "speed_std_avg": float,
                              "mean_lateral_g_avg": float,
                              "max_lateral_g_peak": float,
                              "mean_rpm_avg": float,
                              "idle_ratio": float,
                              "harsh_brake_count": int,
                              "harsh_brake_rate_per_100km": float
                            },
                            "raw_smoothness_logs": {...},
                            "raw_harsh_events": {...}
                          }

      demographics: JSON string from trip context, containing:
                   {
                     "driver_age": int,
                     "experience_level": str
                   }

      xai_engine: SHAPExplainer instance (injected by agent, optional)
      fairness_auditor: FairnessAuditor instance (injected by agent, optional)

    OUTPUT CONTRACT (Strict):
      {
        "trip_id": str,
        "behaviour_score": float (0-100),
        "score_label": str ("Excellent" | "Good" | "Average" | "Below Average" | "Poor"),
        "score_breakdown": {
          "jerk_component": float (0-40),
          "speed_component": float (0-25),
          "lateral_component": float (0-20),
          "engine_component": float (0-15)
        },
        "shap_explanation": {
          "top_features": [...],
          "base_score": float,
          "final_score": float,
          "narrative": str
        },
        "fairness_audit": {
          "demographic_parity": str ("PASS" | "WARN" | "FAIL"),
          "equalized_odds": str ("PASS" | "WARN" | "FAIL"),
          "disparate_impact": float,
          "bias_score": float,
          "bias_detected": bool,
          "recommendation": str
        }
      }

    DEMO: Returns hardcoded (no modules needed)
    PROD (Stage 3-4): Calls modules to compute real values
    """
    # Parse inputs
    try:
        features_data = json.loads(smoothness_features)
        demo_data = json.loads(demographics)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON input"})

    # DEMO VERSION: Return hardcoded (no modules needed)
    if xai_engine is None and fairness_auditor is None:
        return json.dumps(
            {
                "trip_id": trip_id,
                "behaviour_score": DEMO_SCORING_AGENT_TRIP_SCORE["behaviour_score"],
                "score_label": "Good",
                "score_breakdown": {
                    "jerk_component": 28.4,
                    "speed_component": 18.2,
                    "lateral_component": 19.1,
                    "engine_component": 8.6,
                },
                "shap_explanation": DEMO_SCORING_AGENT_SHAP_EXPLANATION,
                "fairness_audit": DEMO_SCORING_AGENT_FAIRNESS_AUDIT,
            }
        )

    # PROD VERSION (Stage 3+):
    # explanation = xai_engine.explain(smoothness_features_dict)
    # audit = fairness_auditor.audit(74.3, demo_demographics)
    # return json.dumps({...})

    # For now, demo version
    return json.dumps(
        {
            "trip_id": trip_id,
            "behaviour_score": DEMO_SCORING_AGENT_TRIP_SCORE["behaviour_score"],
            "score_label": "Good",
            "score_breakdown": {
                "jerk_component": 28.4,
                "speed_component": 18.2,
                "lateral_component": 19.1,
                "engine_component": 8.6,
            },
            "shap_explanation": DEMO_SCORING_AGENT_SHAP_EXPLANATION,
            "fairness_audit": DEMO_SCORING_AGENT_FAIRNESS_AUDIT,
        }
    )


# ==============================================================================
# Tool Registry
# ==============================================================================

SCORING_TOOLS = [
    get_trip_context,  # Read trip context & demographics
    get_smoothness_logs,  # Read raw smoothness windows
    get_harsh_events,  # Read raw harsh events
    extract_scoring_features,  # Aggregate features from raw data
    score_and_audit_trip,  # COMPOSITE: score + explain + audit
]
