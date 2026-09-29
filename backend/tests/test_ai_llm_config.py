from app.ai.providers.gemini import GeminiProvider
from app.api.dependencies import get_llm_provider


def test_default_llm_provider():
    provider = get_llm_provider()

    assert isinstance(provider, GeminiProvider)
