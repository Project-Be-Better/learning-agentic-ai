"""Base agent interface that all agents should implement."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Minimal contract every agent must fulfil."""

    name: str = "base_agent"

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Execute the agent's primary logic and return a result."""
        raise NotImplementedError
