"""
Orchestrator Tools — Event-Driven Routing with EventMatrix

These tools help the OrchestratorAgent make routing decisions:
1. Get event config from EventMatrix (single source of truth)
2. Evaluate coaching rules (deterministic, after scoring)

EventMatrix is the source of truth for what agents should run.
LLM validates and interprets the action field for edge cases.
"""

import json

# Mock Redis client (in prod, this would be real Redis)
import redis
from langchain_core.tools import tool

redis_client = redis.Redis(host="localhost", port=6379, db=0)

# ==============================================================================
# EVENT MATRIX (Source of Truth)
# ==============================================================================
# In production, import from your models/enums:
# from ..models.enums import Priority, EventConfig, EVENT_MATRIX


class Priority:
    """Priority levels (simulated)"""

    CRITICAL = 0
    HIGH = 3
    MEDIUM = 6
    LOW = 9


class EventConfig:
    """Event configuration from EventMatrix"""

    def __init__(self, category: str, priority: int, ml_weight: float, action: str):
        self.category = category
        self.priority = priority
        self.ml_weight = ml_weight
        self.action = action


# EventMatrix: Single source of truth
EVENT_MATRIX: dict[str, EventConfig] = {
    "collision": EventConfig(
        "critical", Priority.CRITICAL, 1.0, "Emergency Alert & 911"
    ),
    "rollover": EventConfig(
        "critical", Priority.CRITICAL, 1.0, "Emergency Alert & 911"
    ),
    "vehicle_offline": EventConfig("critical", Priority.HIGH, 0.3, "Fleet Alert"),
    "harsh_brake": EventConfig("harsh_events", Priority.HIGH, 0.7, "Coaching"),
    "hard_accel": EventConfig("harsh_events", Priority.HIGH, 0.7, "Coaching"),
    "harsh_corner": EventConfig("harsh_events", Priority.HIGH, 0.6, "Coaching"),
    "speeding": EventConfig("speed_compliance", Priority.MEDIUM, 0.5, "Regulatory"),
    "excessive_idle": EventConfig("idle_fuel", Priority.LOW, 0.2, "Coaching"),
    "smoothness_log": EventConfig(
        "normal_operation", Priority.LOW, -0.2, "Reward Bonus"
    ),
    "normal_operation": EventConfig("normal_operation", Priority.LOW, 0.0, "Analytics"),
    "start_of_trip": EventConfig("trip_lifecycle", Priority.LOW, 0.0, "Logging"),
    "end_of_trip": EventConfig("trip_lifecycle", Priority.LOW, 0.0, "Scoring"),
    "driver_sos": EventConfig("critical", Priority.CRITICAL, 0.0, "Emergency Alert"),
    "driver_dispute": EventConfig("driver_feedback", Priority.HIGH, 0.0, "HITL"),
    "driver_complaint": EventConfig("driver_feedback", Priority.HIGH, 0.0, "Support"),
    "driver_feedback": EventConfig(
        "driver_feedback", Priority.MEDIUM, 0.0, "Sentiment"
    ),
    "driver_comment": EventConfig("driver_feedback", Priority.LOW, 0.0, "Sentiment"),
    "malicious_injection": EventConfig(
        "security_scan", Priority.MEDIUM, 0.0, "Reject & Log"
    ),
}

# Action → Agents mapping (tells LLM what each action means)
ACTION_TO_AGENTS = {
    "Emergency Alert & 911": ["safety"],
    "Emergency Alert": ["safety"],
    "Fleet Alert": ["safety"],
    "Coaching": ["scoring", "driver_support"],
    "Regulatory": ["scoring"],
    "Scoring": ["scoring"],
    "Reward Bonus": [],
    "Analytics": [],
    "Logging": [],
    "Sentiment": ["sentiment"],
    "Support": ["driver_support"],
    "HITL": ["human_in_the_loop"],
    "Reject & Log": [],
}


# ==============================================================================
# TOOL 1: Get Event Config from EventMatrix
# ==============================================================================


@tool
def get_event_config(trigger_event_type: str) -> str:
    """
    Look up event in EventMatrix (single source of truth).

    Returns event configuration with:
    - category: Event category (e.g., "critical", "harsh_events", "trip_lifecycle")
    - priority: Event priority (0=CRITICAL, 3=HIGH, 6=MEDIUM, 9=LOW)
    - ml_weight: ML weighting factor for scoring
    - action: What should happen with this event
      * "Emergency Alert & 911" → Safety Agent needed
      * "Coaching" → Scoring + Driver Support Agents needed
      * "Scoring" → Scoring Agent needed
      * "Sentiment" → Sentiment Agent needed
      * "Analytics" → No agents needed, just logging
      * etc.

    Args:
        trigger_event_type: Event type (e.g., "collision", "harsh_brake", "end_of_trip")

    Returns:
        JSON string with event configuration from EventMatrix

    Example Output (harsh_brake):
        {
          "event_type": "harsh_brake",
          "category": "harsh_events",
          "priority": 3,
          "ml_weight": 0.7,
          "action": "Coaching",
          "agents_from_action": ["scoring", "driver_support"],
          "reasoning": "EventMatrix is source of truth"
        }

    Example Output (unknown event):
        {
          "error": "Unknown event type: 'foobar'",
          "available_events": [...],
          "hint": "Use one of the available_events. If new event, add to EventMatrix first."
        }
    """
    event_config = EVENT_MATRIX.get(trigger_event_type)

    if not event_config:
        return json.dumps(
            {
                "error": f"Unknown event type: '{trigger_event_type}'",
                "available_events": sorted(list(EVENT_MATRIX.keys())),
                "hint": "Use one of the available_events. If new event, add to EventMatrix first.",
            }
        )

    # Get agents from action (helper for LLM)
    agents_from_action = ACTION_TO_AGENTS.get(event_config.action, [])

    config = {
        "event_type": trigger_event_type,
        "category": event_config.category,
        "priority": event_config.priority,
        "ml_weight": event_config.ml_weight,
        "action": event_config.action,
        "agents_from_action": agents_from_action,  # Suggested agents from action
        "reasoning": "EventMatrix is the single source of truth for event behavior",
    }

    return json.dumps(config)


# ==============================================================================
# TOOL 2: Evaluate Coaching Rules (Deterministic)
# ==============================================================================


@tool
def evaluate_coaching_rules(
    behaviour_score: float,
    historical_avg: float,
    flagged_events_count: int,
) -> str:
    """
    DETERMINISTIC rule engine: Should Driver Support Agent run?

    Evaluates three coaching rules. ANY rule triggering means coaching is needed.

    Rule 1: Absolute Floor
      IF behaviour_score < 60
      Reasoning: Score below safe threshold, high-risk state requiring intervention

    Rule 2: Negative Trend Detection
      IF |behaviour_score - historical_avg| > 10
      Reasoning: Significant drop from baseline, catching gradual decline

    Rule 3: Flagged Events Present
      IF flagged_events_count > 0
      Reasoning: Safety incidents occurred during trip, context-specific coaching needed

    Args:
        behaviour_score: Trip score from ScoringAgent (0-100)
        historical_avg: Driver's 3-trip rolling average (0-100)
        flagged_events_count: Number of safety-flagged events this trip

    Returns:
        JSON string with coaching decision

    Example Output (All Rules Triggered):
        {
          "coaching_needed": true,
          "triggered_rules": ["absolute_floor", "trend_detection", "flagged_events"],
          "priority_escalation": true,
          "new_priority": 6,
          "reasoning": "Score: 54.2, Avg: 68.4, Events: 2"
        }

    Example Output (No Rules Triggered):
        {
          "coaching_needed": false,
          "triggered_rules": [],
          "priority_escalation": false,
          "new_priority": 9,
          "reasoning": "Score: 78.5, Avg: 76.1, Events: 0"
        }
    """

    triggered_rules = []
    coaching_needed = False

    # Rule 1: Absolute Floor
    if behaviour_score < 60:
        triggered_rules.append("absolute_floor")
        coaching_needed = True

    # Rule 2: Negative Trend Detection
    if abs(behaviour_score - historical_avg) > 10:
        triggered_rules.append("trend_detection")
        coaching_needed = True

    # Rule 3: Flagged Events Present
    if flagged_events_count > 0:
        triggered_rules.append("flagged_events")
        coaching_needed = True

    # Priority escalation
    # If coaching is needed, escalate priority (LOW 9 → MEDIUM 6)
    priority_escalation = coaching_needed
    new_priority = 6 if priority_escalation else 9

    decision = {
        "coaching_needed": coaching_needed,
        "triggered_rules": triggered_rules,
        "priority_escalation": priority_escalation,
        "new_priority": new_priority,
        "reasoning": (
            f"Score: {behaviour_score}, Historical Avg: {historical_avg}, "
            f"Flagged Events: {flagged_events_count}"
        ),
    }

    return json.dumps(decision)


# ==============================================================================
# Tool Registry
# ==============================================================================

ORCHESTRATOR_TOOLS = [
    get_event_config,  # Look up event in EventMatrix
    evaluate_coaching_rules,  # Deterministic coaching rule engine
]
