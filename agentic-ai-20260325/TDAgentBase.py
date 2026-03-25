from abc import ABC, abstractmethod
from typing import Dict, Any, TypedDict
from datetime import datetime, timezone
from enum import StrEnum


class TDAgentEnum(StrEnum):
    SCORING_AGENT = "scoring_agent"
    SAFETY_AGENT = "safety_agent"


class TDAgentState(TypedDict):
    """
    Trip Info + Signed Permission
    """

    trip_id: str
    trip_context: Dict[str, Any]  # Pre-fetched data
    intent_capsule: Dict[str, Any]  # Signed permission slip


class TDAgentBase(ABC):
    """
    Base Class
    """

    def __init__(self, agent_id: TDAgentEnum) -> None:
        """
        Constructor
        """
        self.agent_id = agent_id.value

    @abstractmethod
    def _execute_logic(self, trip_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        The only method that should be overridden
        1. TAKE input
        2. PERFORM work
        3. RETURN output
        """
        return trip_context

    def run(self, state: TDAgentState) -> Dict[str, Any]:
        """
        Public API
        4. CALLS the business logic
        5.
        6. Returns the output as JSON
        Run the agent with Intent Capsule in state.

        State structure:
          - trip_id: "TRIP-001"
          - trip_context: {trip_pings, safety_output, ...}
          - intent_capsule: {capsule_data, signature, ...}
        """
        # Step 1: Your logic (read trip_context only)
        agent_output = self._execute_logic(state["trip_context"])

        # Step 2: Wrap with metadata
        result = {
            "agent": self.agent_id,
            "trip_id": state["trip_id"],
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "intent_capsule": state["intent_capsule"],  # Pass it through
            "output": agent_output,
        }
        return result
