from adapters.anthropic_adapter import AnthropicAdapter
from adapters.models import AnthropicModel, LLMConfig, OpenAIModel
from adapters.openai_adapter import OpenAIAdapter


def _infer_provider_from_model(model: OpenAIModel | AnthropicModel) -> str:
    if isinstance(model, OpenAIModel):
        return "openai"
    return "anthropic"


def load_llm(model: OpenAIModel | AnthropicModel) -> LLMConfig:
    """Factory that accepts a model enum and returns a configured adapter.

    - load_llm(OpenAIModel.GPT_4O)
    - load_llm(AnthropicModel.CLAUDE_35_SONNET_20241022)
    """
    from dotenv import load_dotenv

    load_dotenv()

    resolved_provider = _infer_provider_from_model(model)

    if resolved_provider == "openai":
        adapter = OpenAIAdapter(model=model)
    else:
        adapter = AnthropicAdapter(model=model)

    return LLMConfig(
        provider=resolved_provider,
        model=adapter.model.value,
        adapter=adapter,
    )
