"""
Pydantic models for the agent framework.

Provides type safety, validation, and dot notation access for:
- Agent state (input)
- Agent output (from _execute_logic)
- Agent result (from run())
- Intent Capsule structures
"""

from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import Dict, Any, Optional, List
from datetime import datetime


class CapsuleConstraints(BaseModel):
    """Constraints in the Intent Capsule."""

    allowed_actions: List[str] = Field(
        default=["score_trip"], description="Actions allowed by this capsule"
    )
    resource_id: str = Field(
        description="Resource identifier (e.g., redis:trip_summary:TRIP-001)"
    )
    max_compute_time_seconds: int = Field(
        default=30, description="Maximum compute time allowed"
    )
    max_harsh_events: Optional[int] = Field(
        default=None, description="Optional max harsh events constraint"
    )


class CapsuleData(BaseModel):
    """The actual capsule data (before signing)."""

    correlation_id: str = Field(description="Request correlation ID")
    trip_id: str = Field(description="Trip being processed")
    subject: str = Field(description="Agent name")
    purpose: str = Field(description="What this capsule is for")
    constraints: CapsuleConstraints = Field(description="Capsule constraints")
    issued_at: int = Field(description="Unix timestamp")
    expires_at: int = Field(description="Expiry unix timestamp")


class IntentCapsule(BaseModel):
    """Signed Intent Capsule (work order)."""

    capsule: CapsuleData = Field(description="The capsule data")
    signature: str = Field(description="HMAC-SHA256 signature")


class TDAgentState(BaseModel):
    """
    Trip Info + Signed Permission.

    State passed to agent.run() method.
    Provides clean dot notation: state.trip_id, state.intent_capsule, etc.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    trip_id: str = Field(description="Unique trip identifier")
    trip_context: Dict[str, Any] = Field(
        description="Pre-fetched data (pings, safety output, etc)"
    )
    intent_capsule: IntentCapsule = Field(description="Signed permission slip")


class AgentOutput(BaseModel):
    """
    What agent logic returns.

    Returned by _execute_logic() override.
    Represents the pure computation result.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trip_score": 85,
                "pings_count": 42,
                "harsh_events_count": 3,
                "action": "score_trip",
            }
        }
    )

    trip_score: int = Field(description="Trip score (0-100)")
    pings_count: int = Field(ge=0, description="Number of pings")
    harsh_events_count: int = Field(ge=0, description="Number of harsh events")
    action: str = Field(default="score_trip", description="Action to perform on result")


class AgentResult(BaseModel):
    """
    Full result returned by run().

    Wraps the agent output with metadata:
    - agent_id: Which agent executed
    - trip_id: Which trip was processed
    - timestamp: When execution completed
    - status: Execution status
    - correlation_id: For distributed tracing
    - output: The actual computation result

    Clean access: result.output.trip_score, result.status, etc.
    """

    agent: str = Field(description="Agent ID (e.g., 'scoring_agent')")
    trip_id: str = Field(description="Trip ID processed")
    timestamp: str = Field(
        description="ISO 8601 timestamp with milliseconds (Z suffix)"
    )
    status: str = Field(
        default="success", description="Execution status ('success' or 'failed')"
    )
    correlation_id: str = Field(description="UUID for tracing across services")
    output: AgentOutput = Field(description="Computation result")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "agent": "scoring_agent",
                "trip_id": "TRIP-001",
                "timestamp": "2026-03-26T12:34:56.789Z",
                "status": "success",
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "output": {
                    "trip_score": 85,
                    "pings_count": 42,
                    "harsh_events_count": 3,
                    "action": "score_trip",
                },
            }
        }
    )


TDAgentStateType = TDAgentState
AgentResultType = AgentResult
