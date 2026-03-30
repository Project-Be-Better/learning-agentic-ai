"""
EventConfig with Type-Safe Enums + Unified Security Specs

Single source of truth for:
1. Event routing (which agents run)
2. Security policy (what data can be accessed)
3. Audit requirements (what gets logged)

NO magic strings - everything is Enum or StrEnum.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Set

# ==============================================================================
# ENUMS (Type-Safe, No Magic Strings)
# ==============================================================================


class Priority(Enum):
    """Event priority levels"""

    CRITICAL = 0  # Immediate action required
    HIGH = 3  # Urgent, next available
    MEDIUM = 6  # Standard processing
    LOW = 9  # Batch processing


class Action(Enum):
    """What should happen with this event"""

    EMERGENCY_ALERT_911 = auto()
    EMERGENCY_ALERT = auto()
    FLEET_ALERT = auto()
    COACHING = auto()
    REGULATORY = auto()
    SCORING = auto()
    SENTIMENT = auto()
    SUPPORT = auto()
    HITL = auto()  # Human In The Loop
    ANALYTICS = auto()
    LOGGING = auto()
    REWARD_BONUS = auto()
    REJECT_AND_LOG = auto()


class AgentType(str, Enum):
    """Which agents can run (StrEnum for logging/serialization)"""

    SAFETY = "safety"
    SCORING = "scoring"
    DRIVER_SUPPORT = "driver_support"
    SENTIMENT = "sentiment"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"


class DataKey(str, Enum):
    """What data keys agents can read/write (StrEnum for permissions)"""

    # Read keys (trip context, history, etc.)
    DRIVER_ID = "driver_id"
    TRIP_ID = "trip_id"
    TRUCK_ID = "truck_id"
    TRIP_CONTEXT = "trip_context"
    HISTORICAL_AVG_SCORE = "historical_avg_score"
    PEER_GROUP_AVG = "peer_group_avg"
    FLAGGED_EVENTS = "flagged_events"
    TRIP_DURATION = "trip_duration"
    TRIP_DISTANCE = "trip_distance"

    # Write keys (what agents can create)
    TRIP_SCORES = "trip_scores"
    SHAP_EXPLANATIONS = "shap_explanations"
    FAIRNESS_AUDIT = "fairness_audit"
    COACHING_MESSAGE = "coaching_message"
    COACHING_RULES_TRIGGERED = "coaching_rules_triggered"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SAFETY_ENRICHMENT = "safety_enrichment"
    AUDIT_LOG = "audit_log"


class DataClassification(Enum):
    """How sensitive is the data"""

    PUBLIC = auto()
    INTERNAL = auto()
    SENSITIVE = auto()  # Behavioral data
    RESTRICTED = auto()  # PII, financial


class CapsuleExpiryPolicy(Enum):
    """How long capsule remains valid"""

    IMMEDIATE = 60  # 1 minute
    SHORT = 600  # 10 minutes
    STANDARD = 3600  # 1 hour
    LONG = 86400  # 24 hours


# ==============================================================================
# SECURITY SPECIFICATIONS (Type-Safe)
# ==============================================================================


@dataclass
class ScopeSpecification:
    """Security scope for an event"""

    read_keys: Set[DataKey] = field(default_factory=set)
    """What data this event's agents can read"""

    write_keys: Set[DataKey] = field(default_factory=set)
    """What data this event's agents can write"""

    allowed_agents: Set[AgentType] = field(default_factory=set)
    """Which agents are allowed to run for this event"""

    data_classification: DataClassification = DataClassification.INTERNAL
    """How sensitive is the data involved"""

    requires_audit: bool = False
    """Should this event be logged for audit trail"""

    requires_hmac: bool = True
    """HMAC signing required by DEFAULT (secure by default).
    Only set to False for purely informational events (logging, analytics).
    If ANY data is written or decisions are made, this must be True."""

    capsule_expiry: CapsuleExpiryPolicy = CapsuleExpiryPolicy.STANDARD
    """How long the intent capsule remains valid"""

    step_index_enforced: bool = False
    """Should step_index enforcement be used (sequence validation)"""

    forensic_capture: bool = False
    """Should forensic snapshots be captured on mismatch"""


@dataclass
class EventConfig:
    """
    Event configuration: Unified routing + security governance

    Single source of truth for:
    - What agents run (action + allowed_agents)
    - What data they access (read_keys, write_keys)
    - How it's secured (HMAC, capsule expiry, step_index)
    - How it's audited (requires_audit, forensic_capture)
    """

    # ── ROUTING ───────────────────────────────────────────
    action: Action
    """What should happen (maps to agents)"""

    category: str
    """Event category (critical, harsh_events, trip_lifecycle, etc.)"""

    priority: Priority
    """Event priority (CRITICAL, HIGH, MEDIUM, LOW)"""

    ml_weight: float
    """ML weighting factor for scoring"""

    # ── SECURITY ───────────────────────────────────────────
    scope: ScopeSpecification
    """Security scope (read keys, write keys, allowed agents)"""

    # ── CONVENIENCE PROPERTIES ────────────────────────────
    @property
    def agents_from_action(self) -> List[AgentType]:
        """Get agents that should run based on action"""
        return list(self.scope.allowed_agents)

    @property
    def is_critical(self) -> bool:
        """Is this a critical event"""
        return self.priority == Priority.CRITICAL

    @property
    def requires_security_hardening(self) -> bool:
        """Does this event need extra security"""
        return (
            self.scope.data_classification
            in [DataClassification.SENSITIVE, DataClassification.RESTRICTED]
            or self.scope.requires_hmac
            or self.scope.forensic_capture
        )


# ==============================================================================
# ACTION → AGENTS MAPPING (Type-Safe)
# ==============================================================================

ACTION_TO_AGENTS = {
    Action.EMERGENCY_ALERT_911: {AgentType.SAFETY},
    Action.EMERGENCY_ALERT: {AgentType.SAFETY},
    Action.FLEET_ALERT: {AgentType.SAFETY},
    Action.COACHING: {AgentType.SCORING, AgentType.DRIVER_SUPPORT},
    Action.REGULATORY: {AgentType.SCORING},
    Action.SCORING: {AgentType.SCORING},
    Action.SENTIMENT: {AgentType.SENTIMENT},
    Action.SUPPORT: {AgentType.DRIVER_SUPPORT},
    Action.HITL: {AgentType.HUMAN_IN_THE_LOOP},
    Action.ANALYTICS: set(),
    Action.LOGGING: set(),
    Action.REWARD_BONUS: set(),
    Action.REJECT_AND_LOG: set(),
}


# ==============================================================================
# EVENT MATRIX (Type-Safe, Unified Governance)
# ==============================================================================

EVENT_MATRIX: dict[str, EventConfig] = {
    # ── CRITICAL EVENTS (Emergency Response) ──────────────────────────────
    "collision": EventConfig(
        action=Action.EMERGENCY_ALERT_911,
        category="critical",
        priority=Priority.CRITICAL,
        ml_weight=1.0,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.SAFETY_ENRICHMENT,
                DataKey.AUDIT_LOG,
            },
            allowed_agents={AgentType.SAFETY},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
            requires_hmac=True,
            capsule_expiry=CapsuleExpiryPolicy.IMMEDIATE,
            step_index_enforced=True,
            forensic_capture=True,
        ),
    ),
    "rollover": EventConfig(
        action=Action.EMERGENCY_ALERT_911,
        category="critical",
        priority=Priority.CRITICAL,
        ml_weight=1.0,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.SAFETY_ENRICHMENT,
                DataKey.AUDIT_LOG,
            },
            allowed_agents={AgentType.SAFETY},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
            requires_hmac=True,
            capsule_expiry=CapsuleExpiryPolicy.IMMEDIATE,
            step_index_enforced=True,
            forensic_capture=True,
        ),
    ),
    "driver_sos": EventConfig(
        action=Action.EMERGENCY_ALERT,
        category="critical",
        priority=Priority.CRITICAL,
        ml_weight=1.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys={DataKey.AUDIT_LOG},
            allowed_agents={AgentType.SAFETY},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
            requires_hmac=True,
            capsule_expiry=CapsuleExpiryPolicy.IMMEDIATE,
            forensic_capture=True,
        ),
    ),
    # ── HIGH PRIORITY HARSH EVENTS (Coaching) ────────────────────────────
    "harsh_brake": EventConfig(
        action=Action.COACHING,
        category="harsh_events",
        priority=Priority.HIGH,
        ml_weight=0.7,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.HISTORICAL_AVG_SCORE,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.TRIP_SCORES,
                DataKey.COACHING_MESSAGE,
                DataKey.COACHING_RULES_TRIGGERED,
            },
            allowed_agents={AgentType.SCORING, AgentType.DRIVER_SUPPORT},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
            # requires_hmac=True (default - secure by default)
            capsule_expiry=CapsuleExpiryPolicy.STANDARD,
            step_index_enforced=False,
        ),
    ),
    "hard_accel": EventConfig(
        action=Action.COACHING,
        category="harsh_events",
        priority=Priority.HIGH,
        ml_weight=0.7,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.HISTORICAL_AVG_SCORE,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.TRIP_SCORES,
                DataKey.COACHING_MESSAGE,
                DataKey.COACHING_RULES_TRIGGERED,
            },
            allowed_agents={AgentType.SCORING, AgentType.DRIVER_SUPPORT},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
        ),
    ),
    "harsh_corner": EventConfig(
        action=Action.COACHING,
        category="harsh_events",
        priority=Priority.HIGH,
        ml_weight=0.6,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.HISTORICAL_AVG_SCORE,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.TRIP_SCORES,
                DataKey.COACHING_MESSAGE,
                DataKey.COACHING_RULES_TRIGGERED,
            },
            allowed_agents={AgentType.SCORING, AgentType.DRIVER_SUPPORT},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
        ),
    ),
    "vehicle_offline": EventConfig(
        action=Action.FLEET_ALERT,
        category="critical",
        priority=Priority.HIGH,
        ml_weight=0.3,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRUCK_ID, DataKey.TRIP_ID},
            write_keys={DataKey.SAFETY_ENRICHMENT, DataKey.AUDIT_LOG},
            allowed_agents={AgentType.SAFETY},
            data_classification=DataClassification.INTERNAL,
            requires_audit=True,
            requires_hmac=True,
            capsule_expiry=CapsuleExpiryPolicy.SHORT,
        ),
    ),
    # ── MEDIUM PRIORITY (Regulatory) ──────────────────────────────────────
    "speeding": EventConfig(
        action=Action.REGULATORY,
        category="speed_compliance",
        priority=Priority.MEDIUM,
        ml_weight=0.5,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
            },
            write_keys={DataKey.TRIP_SCORES},
            allowed_agents={AgentType.SCORING},
            data_classification=DataClassification.INTERNAL,
            requires_audit=True,
        ),
    ),
    "driver_feedback": EventConfig(
        action=Action.SENTIMENT,
        category="driver_feedback",
        priority=Priority.MEDIUM,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys={DataKey.SENTIMENT_ANALYSIS},
            allowed_agents={AgentType.SENTIMENT},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
        ),
    ),
    "malicious_injection": EventConfig(
        action=Action.REJECT_AND_LOG,
        category="security_scan",
        priority=Priority.MEDIUM,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys=set(),
            write_keys={DataKey.AUDIT_LOG},
            allowed_agents=set(),
            data_classification=DataClassification.RESTRICTED,
            requires_audit=True,
            requires_hmac=False,
            capsule_expiry=CapsuleExpiryPolicy.IMMEDIATE,
            forensic_capture=True,
        ),
    ),
    # ── LOW PRIORITY (Coaching, Analytics) ──────────────────────────────
    "excessive_idle": EventConfig(
        action=Action.COACHING,
        category="idle_fuel",
        priority=Priority.LOW,
        ml_weight=0.2,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID, DataKey.TRIP_CONTEXT},
            write_keys={DataKey.COACHING_MESSAGE},
            allowed_agents={AgentType.SCORING, AgentType.DRIVER_SUPPORT},
            data_classification=DataClassification.INTERNAL,
            requires_audit=False,
        ),
    ),
    "end_of_trip": EventConfig(
        action=Action.SCORING,
        category="trip_lifecycle",
        priority=Priority.LOW,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={
                DataKey.DRIVER_ID,
                DataKey.TRIP_ID,
                DataKey.TRIP_CONTEXT,
                DataKey.HISTORICAL_AVG_SCORE,
                DataKey.FLAGGED_EVENTS,
            },
            write_keys={
                DataKey.TRIP_SCORES,
                DataKey.SHAP_EXPLANATIONS,
                DataKey.FAIRNESS_AUDIT,
            },
            allowed_agents={AgentType.SCORING},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
            requires_hmac=False,
        ),
    ),
    "start_of_trip": EventConfig(
        action=Action.LOGGING,
        category="trip_lifecycle",
        priority=Priority.LOW,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys={DataKey.AUDIT_LOG},
            allowed_agents=set(),
            data_classification=DataClassification.INTERNAL,
            requires_audit=False,
        ),
    ),
    "smoothness_log": EventConfig(
        action=Action.REWARD_BONUS,
        category="normal_operation",
        priority=Priority.LOW,
        ml_weight=-0.2,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys=set(),
            allowed_agents=set(),
            data_classification=DataClassification.INTERNAL,
            requires_audit=False,
        ),
    ),
    "normal_operation": EventConfig(
        action=Action.ANALYTICS,
        category="normal_operation",
        priority=Priority.LOW,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys=set(),
            allowed_agents=set(),
            data_classification=DataClassification.INTERNAL,
            requires_audit=False,
        ),
    ),
    "driver_complaint": EventConfig(
        action=Action.SUPPORT,
        category="driver_feedback",
        priority=Priority.HIGH,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys={DataKey.COACHING_MESSAGE},
            allowed_agents={AgentType.DRIVER_SUPPORT},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
        ),
    ),
    "driver_dispute": EventConfig(
        action=Action.HITL,
        category="driver_feedback",
        priority=Priority.HIGH,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID, DataKey.TRIP_CONTEXT},
            write_keys={DataKey.AUDIT_LOG},
            allowed_agents={AgentType.HUMAN_IN_THE_LOOP},
            data_classification=DataClassification.SENSITIVE,
            requires_audit=True,
        ),
    ),
    "driver_comment": EventConfig(
        action=Action.SENTIMENT,
        category="driver_feedback",
        priority=Priority.LOW,
        ml_weight=0.0,
        scope=ScopeSpecification(
            read_keys={DataKey.DRIVER_ID, DataKey.TRIP_ID},
            write_keys={DataKey.SENTIMENT_ANALYSIS},
            allowed_agents={AgentType.SENTIMENT},
            data_classification=DataClassification.INTERNAL,
            requires_audit=False,
        ),
    ),
}
