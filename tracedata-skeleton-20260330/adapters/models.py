from enum import StrEnum

from pydantic import BaseModel

from adapters.base import LLMAdapter


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


class LLMConfig(BaseModel):
    """Resolved LLM configuration returned by the factory."""

    provider: str
    model: str
    adapter: LLMAdapter
