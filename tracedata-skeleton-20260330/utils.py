import os
from abc import ABC, abstractmethod

import anthropic
from openai import OpenAI
from pydantic import BaseModel


class LLMAdapter(ABC):
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        """Return a text completion"""
        raise NotImplementedError


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str = "gpt-4o"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY not found in env")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response.choices[0].message.content


class AnthropicAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not found in env")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def complete(self, prompt: str, **kwargs) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1024),
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text


class LLMSetup(BaseModel):
    llm_model: str = "gpt-4"
    llm_client: LLMAdapter


def load_llm() -> LLMSetup:
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        adapter = OpenAIAdapter()
        model = adapter.model

    elif provider == "anthropic":
        adapter = AnthropicAdapter()
        model = adapter.model

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    return LLMSetup(
        llm_model=model,
        llm_client=adapter,
    )
