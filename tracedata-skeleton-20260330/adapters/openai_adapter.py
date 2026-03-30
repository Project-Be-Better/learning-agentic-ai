import os

from adapters.base import LLMAdapter
from adapters.models import OpenAIModel


class OpenAIAdapter(LLMAdapter):
    """OpenAI adapter backed by langchain_openai.ChatOpenAI."""

    DEFAULT_MODEL = OpenAIModel.GPT_4O

    def __init__(self, model: str | OpenAIModel | None = None):
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
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self.model.value,
            temperature=0.4,
        )
