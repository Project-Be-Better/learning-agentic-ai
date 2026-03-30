"""
ScoringAgent Sample Data — Demo Data Contracts

This file contains all sample/demo data used by the ScoringAgent.
It serves two purposes:

1. DOCUMENTATION: Shows teammates what data structures look like
2. TESTING: Provides hardcoded data for demo/unit tests

ORGANIZATION:
  INPUT (Data ScoringAgent Consumes):
    - DEMO_TRIP_CONTEXT — From Orchestrator/DB
    - DEMO_SMOOTHNESS_LOGS — From Redis (populated by Ingestion Tool)
    - DEMO_HARSH_EVENTS — From Redis (populated by Ingestion Tool)

  EXTRACTED (Intermediate - from extract_scoring_features tool):
    - (Implicit - see tools.py)

  OUTPUT (Data ScoringAgent Produces):
    - DEMO_SHAP_EXPLANATION — Stored in scoring.shap_explanations
    - DEMO_FAIRNESS_AUDIT — Stored in scoring.fairness_audit
    - DEMO_TRIP_SCORE — Stored in scoring.trip_scores

Use these to understand cross-agent contracts.
"""

# ==============================================================================
# INPUT DATA — What ScoringAgent Consumes
# ==============================================================================

DEMO_TRIP_CONTEXT = {
    """
    Source: From Orchestrator (reads from Postgres public.trips or Redis)
    Consumed by: get_trip_context() tool
    
    Contains:
      - Trip identification (trip_id, driver_id, truck_id)
      - Trip metadata (duration, distance)
      - Demographics (driver_age, experience_level) — for fairness audit ONLY
      - Baseline context (historical_avg_score, peer_group_avg)
    """
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "truck_id": "T12345",
    # Demographics — used for fairness audit, NOT for scoring
    "driver_age": 28,
    "experience_level": "medium",
    # Context for comparison
    "historical_avg_score": 71.2,  # 3-trip rolling average
    "peer_group_avg": 68.4,  # Same route/shift cohort average
    # Trip metadata — needed for feature extraction
    "duration_minutes": 62,
    "distance_km": 40.3,
    # Logging
    "window_count": 6,
}

"""
    Source: From Redis trip:{id}:smoothness_logs
    Populated by: Ingestion Tool (from device smoothness_log events)
    Consumed by: get_smoothness_logs() tool
    
    Structure: Array of 6-16 10-minute windows
    Each window contains:
      - Spatio-temporal anchor (window_index, trip_meter_km)
      - Acceleration stats (jerk_mean, jerk_max, jerk_std_dev)
      - Speed stats (speed_mean_kmh, speed_std_dev)
      - Lateral stats (mean_lateral_g, max_lateral_g)
      - Engine stats (mean_rpm, idle_seconds)
    
    Used by: extract_scoring_features() to aggregate into scoring features
    """
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

"""
Source: From Redis trip:{id}:harsh_events
Populated by: Ingestion Tool (from device harsh_brake/accel/corner events)
Consumed by: get_harsh_events() tool

Structure: Array of harsh events (0 to many per trip)
Each event contains:
    - Identification (event_id, event_type)
    - Spatio-temporal location (trip_meter_km)
    - Severity (peak_force_g, speed_at_event_kmh)

Used by: extract_scoring_features() to count and calculate per-100km rate

IMPORTANT: Harsh events are for coaching context ONLY.
            They NEVER reduce the behaviour_score.
"""
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
# OUTPUT DATA — What ScoringAgent Produces
# ==============================================================================

DEMO_SHAP_EXPLANATION = {
    """
    Destination: Postgres scoring.shap_explanations table
    Produced by: score_and_audit_trip() tool (from XAI engine)
    
    Contains:
      - Top contributing features and their SHAP values
      - Base score (expected value for average driver)
      - Final score from XGBoost
      - Human-readable narrative
    
    Used by: Frontend (explain endpoint), HITL review, fairness audits
    
    Lifecycle:
      1. Written with explanation_status='pending'
      2. narrate_explanation Celery task runs async
      3. explanation_text filled in, status='done'
    """
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
    """
    Destination: Postgres scoring.fairness_audit table (2 rows per trip)
    Produced by: score_and_audit_trip() tool (from Fairness Auditor)
    
    Contains:
      - Demographic parity checks (equal treatment across age groups)
      - Equalized odds checks (equal false positive/negative rates)
      - Disparate impact ratio (≥0.8 is fair)
      - Bias score (0-1, lower is fairer)
      - Recommendations for flag/review
    
    Used by: Compliance, HITL review, fairness monitoring
    
    Structure: Two rows per trip
      Row 1: protected_attribute='route_type', metric_name='disparate_impact'
      Row 2: protected_attribute='age_group', metric_name='equal_opportunity'
    """
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

DEMO_TRIP_SCORE = {
    """
    Destination: Postgres scoring.trip_scores table
    Produced by: score_and_audit_trip() tool
    
    Contains:
      - Final behaviour_score (0-100, reward model)
      - Smoothness score component
      - Harsh event count (for context/auditing)
      - Model version (for ML model tracking)
      - Fairness pass/fail flag
      - Timestamp (scored_at)
    
    Used by: Public API, Orchestrator decisions, Driver feedback, Analytics
    
    Lifecycle:
      - Written once (immutable source of truth)
      - Never updated (idempotent)
      - One row per trip
    """
    "trip_id": "TRIP-T12345-2026-03-07-08:00",
    "driver_id": "DRV-ANON-7829",
    "behaviour_score": 74.3,
    "smoothness_score": 74.3,
    "harsh_event_count": 4,
    "smoothness_windows": 6,
    "model_version": "xgb_v1.2",
    "fairness_passed": True,
    "disparate_impact": 0.98,
    "scored_at": "2026-03-07T10:45:00Z",
}

# ==============================================================================
# EXTRACTED (Intermediate) — What extract_scoring_features() Produces
# ==============================================================================

DEMO_EXTRACTED_FEATURES = {
    """
    Produced by: extract_scoring_features() tool
    Consumed by: score_and_audit_trip() tool
    
    Contains: Aggregated & calculated features from raw windows + events
    
    Smoothness features:
      - Averages: jerk_mean_avg, speed_std_avg, mean_lateral_g_avg, mean_rpm_avg
      - Peaks: jerk_max_peak, max_lateral_g_peak
      - Ratios: idle_ratio (0-1)
      - Counts: harsh_brake_count, harsh_brake_rate_per_100km
    
    Raw data pass-through:
      - raw_smoothness_logs (for reference/auditing)
      - raw_harsh_events (for reference/auditing)
    """
    "smoothness_features": {
        "jerk_mean_avg": 0.0143,
        "jerk_max_peak": 0.089,
        "speed_std_avg": 12.37,
        "mean_lateral_g_avg": 0.0283,
        "max_lateral_g_peak": 0.22,
        "mean_rpm_avg": 1693,
        "idle_ratio": 0.1505,
        "harsh_brake_count": 4,
        "harsh_brake_rate_per_100km": 9.93,
    },
    "raw_smoothness_logs": {
        "window_count": 6,
        "windows": [],  # Full windows array from DEMO_SMOOTHNESS_LOGS
    },
    "raw_harsh_events": {
        "event_count": 4,
        "events": [],  # Full events array from DEMO_HARSH_EVENTS
    },
}

# ==============================================================================
# SUMMARY: Cross-Agent Data Flow
# ==============================================================================

"""
INCOMING (ScoringAgent consumes):
  From Ingestion Tool:
    → Redis trip:{id}:smoothness_logs ← DEMO_SMOOTHNESS_LOGS
    → Redis trip:{id}:harsh_events ← DEMO_HARSH_EVENTS
  
  From Orchestrator/DB:
    → Postgres public.trips (trip metadata) ← DEMO_TRIP_CONTEXT
    → Postgres safety.trip_safety_summary (Safety Agent output) ← optional in Sprint 3

OUTGOING (ScoringAgent produces):
  → Postgres scoring.trip_scores ← DEMO_TRIP_SCORE
  → Postgres scoring.shap_explanations ← DEMO_SHAP_EXPLANATION
  → Postgres scoring.fairness_audit ← DEMO_FAIRNESS_AUDIT
  → Redis Pub/Sub trip:{id}:events (CompletionEvent) ← score + coaching flag
  → Celery narrate_explanation task (async) ← update explanation_text

INTERMEDIATE (extract_scoring_features produces):
  → DEMO_EXTRACTED_FEATURES (consumed by score_and_audit_trip)
"""
