from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.mock import MockLLMProvider
from app.api.dependencies import get_llm_provider
from app.core.config import settings


def test_default_llm_provider():
    provider = get_llm_provider()

    if settings.llm_provider == "gemini":
        assert isinstance(provider, GeminiProvider)
    else:
        assert isinstance(provider, MockLLMProvider)
