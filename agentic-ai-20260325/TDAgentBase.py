from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime, timezone
from enum import StrEnum
import uuid

from intent_gate import verify_intent_capsule
from logger import get_logger, LogContext
from models import (
    TDAgentState,
    AgentResult,
    AgentOutput,
)


class TDAgentEnum(StrEnum):
    SCORING_AGENT = "scoring_agent"
    SAFETY_AGENT = "safety_agent"


class TDAgentBase(ABC):
    """
    Base Class for all agents with integrated structured logging.
    """

    def __init__(self, agent_id: TDAgentEnum, secret_key: str = "dev_secret") -> None:
        """
        Constructor.

        Args:
            agent_id: Agent type enum
            secret_key: Secret for capsule signing/verification
        """
        self.agent_id = agent_id.value
        self.secret_key = secret_key
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def _execute_logic(self, trip_context: Dict[str, Any]) -> AgentOutput:
        """
        The only method that should be overridden.

        Pure logic returns AgentOutput (validated result).

        1. TAKE input (trip_context)
        2. PERFORM work
        3. RETURN AgentOutput

        Args:
            trip_context: Context dict with trip data

        Returns:
            AgentOutput model with results
        """
        return AgentOutput(
            trip_score=0, pings_count=0, harsh_events_count=0, action="score_trip"
        )

    @verify_intent_capsule
    def run(self, state: TDAgentState) -> AgentResult:
        """
        Run the agent with Intent Capsule in state.

        Pure execution: validate state → execute logic → wrap result.
        Includes structured logging for observability (ELK/PLG compatible).

        State structure:
          - trip_id: "TRIP-001"
          - trip_context: {trip_pings, safety_output, ...}
          - intent_capsule: {capsule_data, signature, ...}

        Args:
            state: The TDAgentState (Pydantic model)

        Returns:
            AgentResult with metadata and output

        Raises:
            ValueError: If trip_context is not a dictionary
            Exception: Any exception from _execute_logic propagates
            TamperingError: If capsule signature is invalid (@verify_intent_capsule)
            ExpirationError: If capsule is expired (@verify_intent_capsule)
        """
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())

        # 1. Validate state structure using dot notation (Pydantic validates on init)
        trip_id = state.trip_id
        trip_context = state.trip_context

        if not isinstance(trip_context, dict):
            self.logger.error(
                "validation_failed",
                status="failed",
                agent_id=self.agent_id,
                trip_id=trip_id,
                correlation_id=correlation_id,
                error="trip_context must be a dictionary",
            )
            raise ValueError("trip_context must be a dictionary")

        # 2. Execute business logic with context tracing
        with LogContext(
            self.logger,
            "agent_execution",
            agent_id=self.agent_id,
            trip_id=trip_id,
            correlation_id=correlation_id,
        ):
            agent_output = self._execute_logic(trip_context)

        # 3. Wrap and return as AgentResult (Pydantic model)
        result = AgentResult(
            agent=self.agent_id,
            trip_id=trip_id,
            timestamp=datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            status="success",
            correlation_id=correlation_id,
            output=agent_output,  # Already AgentOutput model from _execute_logic
        )

        # Log successful execution
        self.logger.info(
            "agent_succeeded",
            status="success",
            agent_id=self.agent_id,
            trip_id=trip_id,
            correlation_id=correlation_id,
            details={"output_keys": list(agent_output.model_dump().keys())},
        )

        return result
