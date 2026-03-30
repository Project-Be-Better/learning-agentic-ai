import os
from typing import Optional

from adapters.anthropic_adapter import AnthropicAdapter
from adapters.models import LLMConfig
from adapters.openai_adapter import OpenAIAdapter


def load_llm(provider: Optional[str] = None, model: Optional[str] = None) -> LLMConfig:
    """Factory that resolves provider/model and returns a configured adapter."""
    from dotenv import load_dotenv

    load_dotenv()

    resolved_provider = (
        os.getenv("LLM_PROVIDER", "openai").lower().strip()
        if provider is None
        else provider.lower().strip()
    )

    if resolved_provider == "openai":
        adapter = OpenAIAdapter(model=model)
    elif resolved_provider == "anthropic":
        adapter = AnthropicAdapter(model=model)
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {resolved_provider}. "
            "Must be one of: openai, anthropic"
        )

    return LLMConfig(
        provider=resolved_provider,
        model=adapter.model.value,
        adapter=adapter,
    )
