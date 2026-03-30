import os
from typing import Any

from adapters.base import LLMAdapter
from adapters.models import AnthropicModel


class AnthropicAdapter(LLMAdapter):
    """Anthropic adapter backed by langchain_anthropic.ChatAnthropic."""

    DEFAULT_MODEL = AnthropicModel.CLAUDE_35_SONNET_20241022

    def __init__(self, model: str | AnthropicModel | None = None):
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
        from langchain_anthropic import ChatAnthropic

        chat_anthropic_cls: Any = ChatAnthropic
        return chat_anthropic_cls(
            model=self.model.value,
            api_key=self.api_key,
            temperature=0.4,
        )
