from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    """Abstract adapter for provider-specific LangChain chat models."""

    @abstractmethod
    def get_chat_model(self) -> Any:
        """Return a LangChain-compatible chat model instance."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.__class__.__name__
