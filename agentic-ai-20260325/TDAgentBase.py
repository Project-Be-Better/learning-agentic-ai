from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime, timezone
from enum import StrEnum
import uuid

from intent_gate import TDAgentState, verify_intent_capsule
from logger import get_logger, LogContext


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
    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        The only method that should be overridden
        1. TAKE input
        2. PERFORM work
        3. RETURN output
        """
        return trip_context

    @verify_intent_capsule
    def run(self, state: TDAgentState) -> Dict[str, Any]:
        """
        Run the agent with Intent Capsule in state.

        Pure execution: validate state → execute logic → wrap result.
        Includes structured logging for observability (ELK/PLG compatible).

        State structure:
          - trip_id: "TRIP-001"
          - trip_context: {trip_pings, safety_output, ...}
          - intent_capsule: {capsule_data, signature, ...}

        Args:
            state: The state dict containing trip info and capsule

        Returns:
            Result dict with agent output and metadata:
            {
                "agent": "scoring_agent",
                "trip_id": "TRIP-001",
                "timestamp": "2026-03-26T..Z",
                "status": "SUCCESS",
                "output": {...}  # Result from _execute_logic
            }

        Raises:
            KeyError: If required fields (trip_id, trip_context) are missing
            ValueError: If trip_context is not a dictionary
            Exception: Any exception from _execute_logic propagates
            TamperingError: If capsule signature is invalid (@verify_intent_capsule)
            ExpirationError: If capsule is expired (@verify_intent_capsule)
        """
        # Generate correlation ID for request tracing
        correlation_id = str(uuid.uuid4())

        # 1. Validate state structure (fail fast)
        trip_id = state["trip_id"]
        trip_context = state["trip_context"]

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

        # 3. Wrap and return
        result = {
            "agent": self.agent_id,
            "trip_id": trip_id,
            "timestamp": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "status": "SUCCESS",
            "output": agent_output,
        }

        # Log successful execution
        self.logger.info(
            "agent_succeeded",
            status="success",
            agent_id=self.agent_id,
            trip_id=trip_id,
            correlation_id=correlation_id,
            details={"output_keys": list(agent_output.keys())},
        )

        return result
