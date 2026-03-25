from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime
from enum import StrEnum
import logging

from intent_gate import TDAgentState, verify_intent_capsule
from exceptions import SecurityError, MissingFieldError

logger = logging.getLogger(__name__)


class TDAgentEnum(StrEnum):
    SCORING_AGENT = "scoring_agent"
    SAFETY_AGENT = "safety_agent"


class TDAgentBase(ABC):
    """
    Base Class
    """

    def __init__(self, agent_id: TDAgentEnum, secret_key: str = "dev_secret") -> None:
        """
        Constructor
        """
        self.agent_id = agent_id.value
        self.secret_key = secret_key

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
        Public API: Run the agent with Intent Capsule in state.

        State structure:
          - trip_id: "TRIP-001"
          - trip_context: {trip_pings, safety_output, ...}
          - intent_capsule: {capsule_data, signature, ...}

        Args:
            state: The state dict containing trip info and capsule

        Returns:
            Result dict with agent output and metadata

        Raises:
            MissingFieldError: If required fields are missing
        """
        # Validate state structure
        try:
            trip_id = state["trip_id"]
            trip_context = state["trip_context"]
        except KeyError as e:
            logger.error(f"Missing required field in state: {e}")
            raise MissingFieldError(f"Missing required field in state: {e}")

        if not isinstance(trip_context, dict):
            logger.error(f"trip_context must be a dict, got {type(trip_context)}")
            raise ValueError("trip_context must be a dictionary")

        logger.debug(f"Running agent {self.agent_id} for trip {trip_id}")

        # Step 1: Execute business logic (read trip_context only)
        try:
            agent_output = self._execute_logic(trip_context)
        except Exception as e:
            logger.error(f"Agent execution failed for trip {trip_id}: {e}")
            raise

        # Step 2: Wrap with metadata
        result = {
            "agent": self.agent_id,
            "trip_id": trip_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "SUCCESS",
            "output": agent_output,
        }

        logger.info(f"Agent {self.agent_id} succeeded for trip {trip_id}")
        return result
