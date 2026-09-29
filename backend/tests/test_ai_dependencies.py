from app.ai.providers.base import LLMProvider
from app.ai.providers.gemini import GeminiProvider
from app.api.dependencies import get_llm_provider


def test_get_llm_provider():
    provider = get_llm_provider()

    assert isinstance(provider, LLMProvider)
    assert isinstance(provider, GeminiProvider)
