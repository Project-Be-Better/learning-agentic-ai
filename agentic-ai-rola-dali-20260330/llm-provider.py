"""
LLM Provider Abstraction Layer
Simplest possible implementation: swap providers without changing agent code.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderCapabilities:
    """Declares what this provider can do."""

    supports_tools: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    max_tokens: int = 4096


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.capabilities = ProviderCapabilities()

    @abstractmethod
    def query(self, prompt: str, **kwargs) -> str:
        """Send a prompt, get a text response."""
        pass

    @abstractmethod
    def has_capability(self, capability: str) -> bool:
        """Check if this provider supports a capability."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"


class OpenAIProvider(LLMProvider):
    """OpenAI (GPT-4, GPT-4-turbo, etc.)"""

    def __init__(self, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model, **kwargs)
        # Import here to allow optional dependency
        from openai import OpenAI

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Declare capabilities
        self.capabilities = ProviderCapabilities(
            supports_tools=True,
            supports_structured_output=True,
            supports_vision=True,
            max_tokens=4096,
        )

    def query(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """Query OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=kwargs.get("max_tokens", 1024),
        )
        return response.choices[0].message.content

    def has_capability(self, capability: str) -> bool:
        """Check capability."""
        return getattr(self.capabilities, f"supports_{capability}", False)


class ClaudeProvider(LLMProvider):
    """Anthropic Claude (Claude 3 Opus, Sonnet, Haiku)"""

    def __init__(self, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(model, **kwargs)
        # Import here to allow optional dependency
        from anthropic import Anthropic

        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Declare capabilities
        self.capabilities = ProviderCapabilities(
            supports_tools=True,
            supports_structured_output=True,
            supports_vision=True,
            max_tokens=4096,
        )

    def query(self, prompt: str, temperature: float = 0.7, **kwargs) -> str:
        """Query Claude API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        # Claude returns content blocks; extract text
        return response.content[0].text

    def has_capability(self, capability: str) -> bool:
        """Check capability."""
        return getattr(self.capabilities, f"supports_{capability}", False)


class ProviderFactory:
    """Simple factory to create providers by name."""

    _providers = {
        "openai": OpenAIProvider,
        "claude": ClaudeProvider,
    }

    @classmethod
    def create(
        cls, provider_name: str, model: Optional[str] = None, **kwargs
    ) -> LLMProvider:
        """
        Create a provider instance.

        Args:
            provider_name: "openai" or "claude"
            model: Optional model override
            **kwargs: Passed to provider __init__

        Returns:
            Initialized LLMProvider subclass
        """
        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown provider: {provider_name}. Available: {list(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]
        if model:
            return provider_class(model=model, **kwargs)
        return provider_class(**kwargs)

    @classmethod
    def register(cls, name: str, provider_class: type):
        """Register a new provider."""
        cls._providers[name] = provider_class
