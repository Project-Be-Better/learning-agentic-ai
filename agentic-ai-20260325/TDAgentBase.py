from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime, timezone
from enum import StrEnum


class TDAgentEnum(StrEnum):
    SCORING_AGENT = "scoring_agent"
    SAFETY_AGENT = "safety_agent"


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
    def _execute_logic(self, sanitized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        The only method that should be overridden
        1. TAKE input
        2. PERFORM work
        3. RETURN output
        """
        return sanitized_data

    def run(self, sanitized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Public API
        4. CALLS the business logic
        5.
        6. Returns the output as JSON
        """

        agent_output = self._execute_logic(sanitized_data)

        result: Dict[str, Any] = {
            "agent": self.agent_id,
            "timestamp": (
                datetime.now(timezone.utc)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z")
            ),
            "output": agent_output,
        }
        return result
