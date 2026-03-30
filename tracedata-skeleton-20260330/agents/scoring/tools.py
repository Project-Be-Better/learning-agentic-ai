"""
Scoring Agent Tools — DEMO VERSION

DEMO APPROACH:
- All tools return HARDCODED JSON responses
- Same interface as production tools
- LLM can still reason about results
- Perfect for demonstrating the pattern

TRANSITION PLAN:
Stage 1 (Now):        Hardcoded responses
Stage 4 (Later):      Swap hardcoded JSON for redis_client.get()
Stage 5 (Later):      Swap hardcoded scoring for domain functions

This approach lets us DEMO the architecture without building everything at once.
"""

import json
from typing import Any

from langchain_core.tools import tool

# ==============================================================================
# HARDCODED DATA (Demo Database)
# ==============================================================================

DEMO_TRIP_CONTEXT = {
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
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
# TOOL 1: Get Trip Context
# ==============================================================================


@tool
def get_trip_context(trip_id: str, redis_client: Any = None) -> str:
    """
    Get trip context from Redis.

    DEMO VERSION: Returns hardcoded data.
    PROD VERSION: Reads from redis_client.get(f"trip:{trip_id}:context")

    Returns: TripContext JSON with driver_id, truck_id, historical_avg_score,
             peer_group_avg, duration_minutes, distance_km, window_count

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    # Hardcoded response for demo
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

    Returns: Array of 6-16 smoothness windows, each with:
    - window_index, trip_meter_km
    - jerk_mean, jerk_max, jerk_std_dev
    - speed_mean_kmh, speed_std_dev
    - mean_lateral_g, max_lateral_g
    - mean_rpm, idle_seconds

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    # Hardcoded response for demo
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

    Returns: Array of harsh events, each with:
    - event_id, event_type (harsh_brake, harsh_accel, harsh_corner)
    - trip_meter_km, peak_force_g, speed_at_event_kmh

    Args:
        trip_id: Unique trip identifier (ignored in demo)
        redis_client: Redis client instance (will be used in prod)
    """
    # Hardcoded response for demo
    return json.dumps(
        {"event_count": len(DEMO_HARSH_EVENTS), "events": DEMO_HARSH_EVENTS}
    )


# ==============================================================================
# TOOL 4: Compute Behaviour Score (Domain Function)
# ==============================================================================


@tool
def compute_behaviour_score(
    jerk_mean_avg: float,
    jerk_max_peak: float,
    speed_std_avg: float,
    mean_lateral_g_avg: float,
    max_lateral_g_peak: float,
    mean_rpm_avg: float,
    idle_ratio: float,
) -> str:
    """
    Compute trip behaviour score from smoothness features.

    DEMO VERSION: Returns hardcoded score (74.3, Good).
    PROD VERSION: Runs XGBoost model with features (Stage 3).

    Score is 0-100. Based on:
    - Jerk (acceleration/braking smoothness): 40 pts
    - Speed consistency: 25 pts
    - Lateral smoothness (cornering): 20 pts
    - Engine discipline: 15 pts

    Args:
        jerk_mean_avg: Mean jerk across all windows (m/s³)
        jerk_max_peak: Peak jerk in any window (m/s³)
        speed_std_avg: Speed standard deviation (km/h)
        mean_lateral_g_avg: Mean lateral acceleration (g)
        max_lateral_g_peak: Peak lateral acceleration (g)
        mean_rpm_avg: Mean RPM
        idle_ratio: Ratio of idle time to total trip time

    Returns: JSON with behaviour_score, score_label, breakdown
    """
    # DEMO: Return hardcoded score
    # (Demonstrates that LLM will still reason about this output)
    return json.dumps(
        {
            "behaviour_score": 74.3,
            "score_label": "Good",
            "breakdown": {
                "jerk_component": 28.4,
                "speed_component": 18.2,
                "lateral_component": 19.1,
                "engine_component": 8.6,
            },
        }
    )


# ==============================================================================
# Tool Registry
# ==============================================================================

SCORING_TOOLS = [
    get_trip_context,
    get_smoothness_logs,
    get_harsh_events,
    compute_behaviour_score,
]
