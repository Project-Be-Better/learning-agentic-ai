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
from enum import StrEnum
from typing import Any, Optional

from pydantic import BaseModel

# =============================================================================
# SECTION 1: LLM ADAPTER ABC (Base class for all providers)
# =============================================================================


class OpenAIModel(StrEnum):
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_35_TURBO = "gpt-3.5-turbo"


class AnthropicModel(StrEnum):
    CLAUDE_OPUS_20250514 = "claude-opus-20250514"
    CLAUDE_SONNET_4_20250514 = "claude-sonnet-4-20250514"
    CLAUDE_35_SONNET_20241022 = "claude-3-5-sonnet-20241022"
    CLAUDE_35_HAIKU_20241022 = "claude-3-5-haiku-20241022"
    CLAUDE_3_OPUS_20240229 = "claude-3-opus-20240229"
    CLAUDE_3_SONNET_20240229 = "claude-3-sonnet-20240229"
    CLAUDE_3_HAIKU_20240307 = "claude-3-haiku-20240307"


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

    Model configuration priority (highest to lowest):
    1. Constructor parameter: OpenAIAdapter(model="gpt-4-turbo")
    2. Environment variable: OPENAI_MODEL=gpt-4-turbo
    3. Default: "gpt-4o"
    """

    # Default model (can be overridden)
    DEFAULT_MODEL = OpenAIModel.GPT_4O

    def __init__(self, model: str | OpenAIModel | None = None):
        """
        Initialize OpenAI adapter.

        Model selection (in order of priority):
        1. Constructor parameter (most specific)
        2. Environment variable OPENAI_MODEL
        3. Class default (DEFAULT_MODEL)

        Args:
            model: OpenAI model name (optional)
                   If None, uses env var or default
                   Examples: "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"

        Raises:
            EnvironmentError: If OPENAI_API_KEY not set
            ValueError: If model is not in AVAILABLE_MODELS

        Examples:
            # Use default (gpt-4o)
            adapter = OpenAIAdapter()

            # Override with env var
            adapter = OpenAIAdapter()  # Uses OPENAI_MODEL env var if set

            # Override with parameter (highest priority)
            adapter = OpenAIAdapter(model="gpt-4-turbo")
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "OPENAI_API_KEY not found in environment. "
                "Set it in .env.local or as environment variable."
            )

        raw_model = (
            model
            if model is not None
            else os.getenv("OPENAI_MODEL", self.DEFAULT_MODEL.value)
        )

        try:
            self.model = (
                raw_model
                if isinstance(raw_model, OpenAIModel)
                else OpenAIModel(raw_model)
            )
        except ValueError:
            available = ", ".join(m.value for m in OpenAIModel)
            raise ValueError(
                f"Invalid OpenAI model: {raw_model}. Available models: {available}"
            )

        self.api_key = api_key

    def get_chat_model(self):
        """
        Return a LangChain ChatOpenAI instance.

        Returns:
            ChatOpenAI: Ready to use with create_react_agent
        """
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model.value,
            temperature=0.4,
        )


# =============================================================================
# SECTION 3: ANTHROPIC ADAPTER
# =============================================================================


class AnthropicAdapter(LLMAdapter):
    """
    Anthropic/Claude adapter.

    Uses langchain_anthropic.ChatAnthropic for LangGraph compatibility.

    Model configuration priority (highest to lowest):
    1. Constructor parameter: AnthropicAdapter(model="claude-opus-20250514")
    2. Environment variable: ANTHROPIC_MODEL=claude-opus-20250514
    3. Default: "claude-3-5-sonnet-20241022"
    """

    # Default model (can be overridden)
    DEFAULT_MODEL = AnthropicModel.CLAUDE_35_SONNET_20241022

    def __init__(self, model: str | AnthropicModel | None = None):
        """
        Initialize Anthropic adapter.

        Model selection (in order of priority):
        1. Constructor parameter (most specific)
        2. Environment variable ANTHROPIC_MODEL
        3. Class default (DEFAULT_MODEL)

        Args:
            model: Anthropic model name (optional)
                   If None, uses env var or default
                   Examples: "claude-opus-20250514", "claude-3-5-sonnet-20241022"

        Raises:
            EnvironmentError: If ANTHROPIC_API_KEY not set
            ValueError: If model is not in AVAILABLE_MODELS

        Examples:
            # Use default (claude-3-5-sonnet-20241022)
            adapter = AnthropicAdapter()

            # Override with env var
            adapter = AnthropicAdapter()  # Uses ANTHROPIC_MODEL env var if set

            # Override with parameter (highest priority)
            adapter = AnthropicAdapter(model="claude-opus-20250514")
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Set it in .env.local or as environment variable."
            )

        raw_model = (
            model
            if model is not None
            else os.getenv("ANTHROPIC_MODEL", self.DEFAULT_MODEL.value)
        )

        try:
            self.model = (
                raw_model
                if isinstance(raw_model, AnthropicModel)
                else AnthropicModel(raw_model)
            )
        except ValueError:
            available = ", ".join(m.value for m in AnthropicModel)
            raise ValueError(
                f"Invalid Anthropic model: {raw_model}. Available models: {available}"
            )

        self.api_key = api_key

    def get_chat_model(self):
        """
        Return a LangChain ChatAnthropic instance.

        Returns:
            ChatAnthropic: Ready to use with create_react_agent
        """
        from langchain_anthropic import ChatAnthropic

        # Some local type stubs infer an incompatible constructor signature.
        # Use Any alias so runtime kwargs remain provider-accurate.
        chat_anthropic_cls: Any = ChatAnthropic
        return chat_anthropic_cls(
            model=self.model.value,
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


def load_llm(provider: Optional[str] = None, model: Optional[str] = None) -> LLMConfig:
    """
    Load LLM adapter based on configuration.

    Configuration priority (highest to lowest):
    1. Function parameters: load_llm(provider="anthropic", model="claude-opus-...")
    2. Environment variables: LLM_PROVIDER, OPENAI_MODEL, ANTHROPIC_MODEL
    3. Defaults: provider="openai", model per adapter's DEFAULT_MODEL

    Environment variables:
        LLM_PROVIDER: "openai" or "anthropic" (default: "openai")
        OPENAI_API_KEY: Required if provider is "openai"
        ANTHROPIC_API_KEY: Required if provider is "anthropic"
        OPENAI_MODEL: OpenAI model (default: gpt-4o)
        ANTHROPIC_MODEL: Anthropic model (default: claude-3-5-sonnet-20241022)

    Args:
        provider: "openai" or "anthropic" (optional)
                  If None, uses LLM_PROVIDER env var or defaults to "openai"
        model: Specific model to use (optional)
               If None, uses provider's OPENAI_MODEL/ANTHROPIC_MODEL env var
               or adapter's DEFAULT_MODEL

    Returns:
        LLMConfig: Initialized configuration with adapter and model info

    Raises:
        ValueError: If provider is unsupported
        EnvironmentError: If required API key is missing

    Examples:
        # Use defaults
        config = load_llm()

        # Use environment variables
        config = load_llm()  # LLM_PROVIDER=anthropic, ANTHROPIC_MODEL=claude-opus-...

        # Override provider only (uses that provider's default model)
        config = load_llm(provider="anthropic")

        # Override provider and model explicitly
        config = load_llm(provider="openai", model="gpt-4-turbo")

        # For tests/scripts
        config = load_llm(provider="anthropic", model="claude-opus-20250514")
        llm = config.adapter.get_chat_model()
    """
    from dotenv import load_dotenv

    # Load from .env.local if it exists
    load_dotenv()

    # Determine provider (priority: param > env > default)
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "openai").lower().strip()
    else:
        provider = provider.lower().strip()

    # Create adapter based on provider
    if provider == "openai":
        adapter = OpenAIAdapter(model=model)

    elif provider == "anthropic":
        adapter = AnthropicAdapter(model=model)

    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {provider}. Must be one of: openai, anthropic"
        )

    return LLMConfig(
        provider=provider,
        model=adapter.model.value,
        adapter=adapter,
    )


# =============================================================================
# SECTION 6: USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    # Example: Load LLM and create a simple agent
    print("\n" + "=" * 70)
    print("LLM Adapter Pattern: Model Configuration Options")
    print("=" * 70 + "\n")

    # EXAMPLE 1: Use defaults
    print("[Example 1] Use Defaults")
    print("-" * 70)
    try:
        config = load_llm()
        print(f"✓ Loaded: {config.provider} ({config.model})\n")
    except Exception as e:
        print(f"Note: {e}\n")

    # EXAMPLE 2: Override via environment (simulated)
    print("[Example 2] Environment Variable Override")
    print("-" * 70)
    print("# In .env.local:")
    print("LLM_PROVIDER=anthropic")
    print("ANTHROPIC_MODEL=claude-opus-20250514")
    print("# Then: config = load_llm()")
    print("# Result: Uses Claude Opus instead of Sonnet\n")

    # EXAMPLE 3: Override via constructor parameter
    print("[Example 3] Constructor Parameter Override")
    print("-" * 70)
    try:
        adapter = AnthropicAdapter(model="claude-opus-20250514")
        print(f"✓ Created adapter with: {adapter.model}\n")
    except Exception as e:
        print(f"Note: {e}\n")

    # EXAMPLE 4: Override via factory function
    print("[Example 4] Factory Function with Parameters")
    print("-" * 70)
    try:
        config = load_llm(provider="openai", model="gpt-4-turbo")
        print(f"✓ Loaded: {config.provider} ({config.model})\n")
    except Exception as e:
        print(f"Note: {e}\n")

    # EXAMPLE 5: For tests/scripts
    print("[Example 5] For Tests/Scripts (Explicit Control)")
    print("-" * 70)
    print("""
    # In unit test:
    config = load_llm(provider="anthropic", model="claude-3-5-haiku-20241022")
    llm = config.adapter.get_chat_model()
    
    agent = ScoringAgent(llm=llm)
    result = agent.invoke(test_input)
    """)

    # EXAMPLE 6: Show available models
    print("\n[Example 6] Available Models")
    print("-" * 70)
    print(f"OpenAI Models: {', '.join(m.value for m in OpenAIModel)}")
    print(f"\nAnthropic Models: {', '.join(m.value for m in AnthropicModel)}\n")
