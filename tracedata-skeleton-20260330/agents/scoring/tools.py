"""
Scoring Agent Tools — DEMO VERSION with Composite Score + Explain + Audit

DEMO APPROACH:
- All tools return HARDCODED JSON responses
- Score, explanation, and audit always run together (one composite tool)
- LLM can still reason about results
- Perfect for demonstrating the pattern with XAI + Fairness

TOOLS:
1. get_trip_context() — Read trip context
2. get_smoothness_logs() — Read smoothness data
3. get_harsh_events() — Read harsh events
4. score_and_audit_trip() — COMPOSITE: Score + Explain (SHAP) + Audit (Fairness)

TRANSITION PLAN:
Stage 1 (Now):        Hardcoded responses
Stage 3 (Later):      Swap score + explanation for real XGBoost + SHAP
Stage 4 (Later):      Swap fairness audit for real AIF360
Stage 5 (Later):      Wire full pipeline

This approach lets us DEMO the architecture without building everything at once.
"""

import json
from typing import Any, Dict

from langchain_core.tools import tool

# ==============================================================================
# HARDCODED DATA (Demo Database) — INPUT TOOLS
# ==============================================================================

DEMO_TRIP_CONTEXT = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    "driver_age": 28,
    "experience_level": "medium",
    "historical_avg_score": 71.2,
    "peer_group_avg": 68.4,
    "duration_minutes": 62,
    "distance_km": 40.3,
    "window_count": 6,
}

DEMO_SMOOTHNESS_LOGS = [
    {
        "window_index": 0,
        "trip_meter_km": 5.2,
        "jerk_mean": 0.018,
        "jerk_max": 0.072,
        "jerk_std_dev": 0.014,
        "speed_mean_kmh": 38.4,
        "speed_std_dev": 14.2,
        "mean_lateral_g": 0.04,
        "max_lateral_g": 0.22,
        "mean_rpm": 1640,
        "idle_seconds": 85,
    },
    {
        "window_index": 1,
        "trip_meter_km": 13.8,
        "jerk_mean": 0.007,
        "jerk_max": 0.031,
        "jerk_std_dev": 0.005,
        "speed_mean_kmh": 82.1,
        "speed_std_dev": 6.8,
        "mean_lateral_g": 0.02,
        "max_lateral_g": 0.11,
        "mean_rpm": 1880,
        "idle_seconds": 0,
    },
    {
        "window_index": 2,
        "trip_meter_km": 22.1,
        "jerk_mean": 0.009,
        "jerk_max": 0.038,
        "jerk_std_dev": 0.007,
        "speed_mean_kmh": 79.3,
        "speed_std_dev": 9.1,
        "mean_lateral_g": 0.02,
        "max_lateral_g": 0.14,
        "mean_rpm": 1820,
        "idle_seconds": 0,
    },
    {
        "window_index": 3,
        "trip_meter_km": 29.4,
        "jerk_mean": 0.024,
        "jerk_max": 0.089,
        "jerk_std_dev": 0.019,
        "speed_mean_kmh": 54.2,
        "speed_std_dev": 18.6,
        "mean_lateral_g": 0.03,
        "max_lateral_g": 0.19,
        "mean_rpm": 1720,
        "idle_seconds": 42,
    },
    {
        "window_index": 4,
        "trip_meter_km": 35.8,
        "jerk_mean": 0.016,
        "jerk_max": 0.061,
        "jerk_std_dev": 0.012,
        "speed_mean_kmh": 41.2,
        "speed_std_dev": 12.4,
        "mean_lateral_g": 0.03,
        "max_lateral_g": 0.21,
        "mean_rpm": 1580,
        "idle_seconds": 58,
    },
    {
        "window_index": 5,
        "trip_meter_km": 40.3,
        "jerk_mean": 0.012,
        "jerk_max": 0.048,
        "jerk_std_dev": 0.009,
        "speed_mean_kmh": 28.1,
        "speed_std_dev": 11.8,
        "mean_lateral_g": 0.02,
        "max_lateral_g": 0.16,
        "mean_rpm": 1420,
        "idle_seconds": 94,
    },
]

DEMO_HARSH_EVENTS = [
    {
        "event_id": "EV-001",
        "event_type": "harsh_brake",
        "trip_meter_km": 4.1,
        "peak_force_g": -0.52,
        "speed_at_event_kmh": 42.0,
    },
    {
        "event_id": "EV-002",
        "event_type": "harsh_brake",
        "trip_meter_km": 28.7,
        "peak_force_g": -0.71,
        "speed_at_event_kmh": 67.2,
    },
    {
        "event_id": "EV-003",
        "event_type": "harsh_brake",
        "trip_meter_km": 29.1,
        "peak_force_g": -0.64,
        "speed_at_event_kmh": 61.8,
    },
    {
        "event_id": "EV-004",
        "event_type": "harsh_brake",
        "trip_meter_km": 33.2,
        "peak_force_g": -0.48,
        "speed_at_event_kmh": 38.5,
    },
]

# ==============================================================================
# HARDCODED DATA (Demo Database) — COMPOSITE TOOL (Score + Explain + Audit)
# ==============================================================================

DEMO_SHAP_EXPLANATION = {
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
        "Excessive idle time (-0.08) slightly reduces the score. "
        "Overall: Good smoothness and control. Score is 74.3 (Good)."
    ),
}

DEMO_FAIRNESS_AUDIT = {
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

    DEMO VERSION: Returns hardcoded 6 windows.
    PROD VERSION: Reads from redis_client.lrange(f"trip:{trip_id}:smoothness_logs", 0, -1)

    Returns: Array of 6-16 smoothness windows with jerk, speed, RPM, idle metrics

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    return json.dumps(
        {"window_count": len(DEMO_SMOOTHNESS_LOGS), "windows": DEMO_SMOOTHNESS_LOGS}
    )


# ==============================================================================
# TOOL 3: Get Harsh Events
# ==============================================================================


@tool
def get_harsh_events(trip_id: str, redis_client: Any = None) -> str:
    """
    Get harsh events (braking, acceleration, cornering) from Redis.

    DEMO VERSION: Returns hardcoded 4 harsh brakes.
    PROD VERSION: Reads from redis_client.lrange(f"trip:{trip_id}:harsh_events", 0, -1)

    Returns: Array of harsh events with event_type, peak_force_g, speed_at_event_kmh

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    return json.dumps(
        {"event_count": len(DEMO_HARSH_EVENTS), "events": DEMO_HARSH_EVENTS}
    )


# ==============================================================================
# TOOL 4: COMPOSITE TOOL — Score + Explain (SHAP) + Audit (Fairness)
# ==============================================================================


@tool
def score_and_audit_trip(
    trip_id: str,
    features: Dict = None,
    demographics: Dict = None,
    xai_engine: Any = None,
    fairness_auditor: Any = None,
) -> str:
    """
    Complete scoring operation: Score the trip + Explain with SHAP + Audit for fairness.

    COMPOSITE TOOL: This is the main operation that always runs together.

    DEMO VERSION: Returns hardcoded score, explanation, and audit
    PROD VERSION (Stage 3+):
      - Compute behaviour score using XGBoost
      - Explain with SHAP values
      - Audit fairness with AIF360

    Returns: JSON with three sections:
      - behaviour_score: Numeric 0-100
      - score_label: Excellent/Good/Average/Below Average/Poor
      - shap_explanation: Top features contributing to score
      - fairness_audit: Demographic bias checks

    Args:
        trip_id: Trip identifier
        features: Feature dictionary (jerk_mean, speed_std_dev, etc.)
        demographics: Demographics dict (driver_age, experience_level, etc.)
        xai_engine: SHAPExplainer instance (will be injected by agent)
        fairness_auditor: FairnessAuditor instance (will be injected by agent)
    """
    # DEMO VERSION: Return hardcoded (no modules needed)
    if xai_engine is None and fairness_auditor is None:
        return json.dumps(
            {
                "trip_id": trip_id,
                "behaviour_score": 74.3,
                "score_label": "Good",
                "score_breakdown": {
                    "jerk_component": 28.4,
                    "speed_component": 18.2,
                    "lateral_component": 19.1,
                    "engine_component": 8.6,
                },
                "shap_explanation": DEMO_SHAP_EXPLANATION,
                "fairness_audit": DEMO_FAIRNESS_AUDIT,
            }
        )

    # PROD VERSION (Stage 3+):
    # score = xai_engine.explain(features) if xai_engine else {"score": 74.3}
    # audit = fairness_auditor.audit(score["score"], demographics) if fairness_auditor else {}
    # return json.dumps({
    #     "trip_id": trip_id,
    #     "behaviour_score": score["score"],
    #     "score_label": score["label"],
    #     "shap_explanation": score.get("explanation", {}),
    #     "fairness_audit": audit
    # })

    # For now, demo version
    return json.dumps(
        {
            "trip_id": trip_id,
            "behaviour_score": 74.3,
            "score_label": "Good",
            "score_breakdown": {
                "jerk_component": 28.4,
                "speed_component": 18.2,
                "lateral_component": 19.1,
                "engine_component": 8.6,
            },
            "shap_explanation": DEMO_SHAP_EXPLANATION,
            "fairness_audit": DEMO_FAIRNESS_AUDIT,
        }
    )


# ==============================================================================
# Tool Registry
# ==============================================================================

SCORING_TOOLS = [
    get_trip_context,
    get_smoothness_logs,
    get_harsh_events,
    score_and_audit_trip,  # ← Composite tool: Score + Explain + Audit
]
