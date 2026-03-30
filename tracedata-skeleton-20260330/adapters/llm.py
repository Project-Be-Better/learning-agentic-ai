"""
LLM Adapter Pattern: Abstract provider differences

This module provides:
- LLMAdapter ABC: Base class for all LLM providers
- OpenAIAdapter: OpenAI/GPT implementation
- AnthropicAdapter: Anthropic/Claude implementation
- load_llm(): Factory function for instantiation

Usage:
    from llm_adapter import load_llm

    llm = load_llm()  # Returns ChatOpenAI or ChatAnthropic based on env

    from langchain_core.tools import tool
    from langgraph.precompiled import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=[tool1, tool2],
        system_prompt="..."
    )

File location:
    Option A: adapters/llm.py (cleaner, dedicated module)
    Option B: utils.py (simpler, all utilities together)

    This file assumes: adapters/llm.py or utils.py
"""

import os
from abc import ABC, abstractmethod

from pydantic import BaseModel

# =============================================================================
# SECTION 1: LLM ADAPTER ABC (Base class for all providers)
# =============================================================================


class LLMAdapter(ABC):
    """
    Abstract base class for LLM providers.

    Provides unified interface for different LLM backends.
    Subclasses implement get_chat_model() to return LangChain chat objects.
    """

    @abstractmethod
    def get_chat_model(self):
        """
        Return a LangChain chat model instance.

        Must return either:
        - ChatOpenAI (from langchain_openai)
        - ChatAnthropic (from langchain_anthropic)
        - Other compatible LangChain chat model

        This is what create_react_agent expects.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"


# =============================================================================
# SECTION 2: OPENAI ADAPTER
# =============================================================================


class OpenAIAdapter(LLMAdapter):
    """
    OpenAI/GPT adapter.

    Uses langchain_openai.ChatOpenAI for LangGraph compatibility.
    """

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize OpenAI adapter.

        Args:
            model: OpenAI model name (default: gpt-4o)

        Raises:
            EnvironmentError: If OPENAI_API_KEY not set
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found in environment. "
                "Set it in .env.local or as environment variable."
            )

        self.model = model
        self.api_key = api_key

    def get_chat_model(self):
        """
        Return a LangChain ChatOpenAI instance.

        Returns:
            ChatOpenAI: Ready to use with create_react_agent
        """
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=0.4,
        )


# =============================================================================
# SECTION 3: ANTHROPIC ADAPTER
# =============================================================================


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic/Claude adapter.

    Uses langchain_anthropic.ChatAnthropic for LangGraph compatibility.
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Anthropic adapter.

        Args:
            model: Anthropic model name (default: claude-3-5-sonnet-20241022)

        Raises:
            EnvironmentError: If ANTHROPIC_API_KEY not set
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Set it in .env.local or as environment variable."
            )

        self.model = model
        self.api_key = api_key

    def get_chat_model(self):
        """
        Return a LangChain ChatAnthropic instance.

        Returns:
            ChatAnthropic: Ready to use with create_react_agent
        """
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=self.model,
            api_key=self.api_key,
            temperature=0.4,
        )


# =============================================================================
# SECTION 4: LLM CONFIGURATION
# =============================================================================


class LLMConfig(BaseModel):
    """
    Configuration container for LLM setup.

    Attributes:
        provider: LLM provider name (e.g., "openai", "anthropic")
        model: Model identifier (e.g., "gpt-4o", "claude-3-5-sonnet-...")
        adapter: LLMAdapter instance
    """

    provider: str
    model: str
    adapter: LLMAdapter


# =============================================================================
# SECTION 5: FACTORY FUNCTION
# =============================================================================


def load_llm() -> LLMConfig:
    """
    Load LLM adapter based on environment configuration.

    Environment variables:
        LLM_PROVIDER: "openai" or "anthropic" (default: "openai")
        OPENAI_API_KEY: Required if provider is "openai"
        ANTHROPIC_API_KEY: Required if provider is "anthropic"
        OPENAI_MODEL: OpenAI model (default: gpt-4o)
        ANTHROPIC_MODEL: Anthropic model (default: claude-3-5-sonnet-20241022)

    Returns:
        LLMConfig: Initialized configuration with adapter and model info

    Raises:
        ValueError: If provider is unsupported
        EnvironmentError: If required API key is missing

    Example:
        config = load_llm()
        llm = config.adapter.get_chat_model()

        agent = create_react_agent(
            model=llm,
            tools=[...],
            system_prompt="..."
        )
    """
    from dotenv import load_dotenv

    # Load from .env.local if it exists
    load_dotenv()

    # Get provider from environment
    provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()

    if provider == "openai":
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        adapter = OpenAIAdapter(model=model)

    elif provider == "anthropic":
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        adapter = AnthropicAdapter(model=model)

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {provider}. Must be one of: openai, anthropic"
        )

    return LLMConfig(
        provider=provider,
        model=adapter.model,
        adapter=adapter,
    )


# =============================================================================
# SECTION 6: USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Example: Load LLM and create a simple agent
    print("\n" + "=" * 70)
    print("LLM Adapter Pattern: Usage Example")
    print("=" * 70 + "\n")

    try:
        config = load_llm()
        print("✓ Loaded LLM Config:")
        print(f"  Provider: {config.provider}")
        print(f"  Model: {config.model}")
        print(f"  Adapter: {config.adapter}\n")

        # Get the chat model
        llm = config.adapter.get_chat_model()
        print(f"✓ Chat Model Ready: {llm}\n")

        # This is what you'd pass to create_react_agent
        print(f"✓ Ready for: create_react_agent(model={llm}, tools=[...], ...)\n")

    except EnvironmentError as e:
        print(f"✗ Environment Error: {e}\n")
        print("Setup .env.local with:")
        print("  LLM_PROVIDER=anthropic")
        print("  ANTHROPIC_API_KEY=sk-ant-...\n")

    except ValueError as e:
        print(f"✗ Configuration Error: {e}\n")
