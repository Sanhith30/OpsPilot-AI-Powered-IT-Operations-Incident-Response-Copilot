import pytest

from app.ai.providers.config import LLMConfig
from app.ai.providers.factory import create_llm_provider
from app.ai.providers.mock import MockLLMProvider


def test_create_mock_provider():
    config = LLMConfig(
        provider="mock",
        model="mock-model",
    )

    provider = create_llm_provider(config)

    assert isinstance(provider, MockLLMProvider)


def test_mock_provider_generates_response():
    provider = MockLLMProvider()

    response = provider.generate(
        system_prompt="You are an incident investigation assistant.",
        user_prompt="Investigate incident INC-1042.",
    )

    assert isinstance(response, str)
    assert response != ""


def test_config_defaults():
    config = LLMConfig()

    assert config.provider == "mock"
    assert config.temperature == 0.0
    assert config.timeout_seconds == 30


def test_unsupported_provider_raises():
    config = LLMConfig(provider="nonexistent")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm_provider(config)


def test_create_gemini_provider():
    from app.ai.providers.gemini import GeminiProvider

    config = LLMConfig(
        provider="gemini",
        model="gemini-3.8-flash",
        api_key="test-api-key",
    )

    provider = create_llm_provider(config)

    assert isinstance(provider, GeminiProvider)
    assert provider.api_key == "test-api-key"
    assert provider.config.model == "gemini-3.8-flash"


def test_create_gemini_provider_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    config = LLMConfig(
        provider="gemini",
        api_key=None,
    )

    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        create_llm_provider(config)


