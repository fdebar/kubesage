# tests/ai/test_factory.py

from unittest.mock import MagicMock, patch

import pytest

from kubesage.ai.enums import AIProviderType
from kubesage.ai.factory import create_ai_provider
from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.utils.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        ai_provider=AIProviderType.OLLAMA,
        ai_model="qwen3",
        ai_url="http://ollama:11434/v1",
        ai_api_key="ollama",
    )


def test_create_ollama_provider(settings: Settings) -> None:
    provider = create_ai_provider(settings)

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._model == "qwen3"


def test_create_openai_provider(settings: Settings) -> None:
    settings.ai_provider = AIProviderType.OPEN_AI
    settings.ai_url = "https://api.openai.com/v1"
    settings.ai_api_key = "test-api-key"

    provider = create_ai_provider(settings)

    assert isinstance(provider, OpenAICompatibleProvider)
    assert provider._model == "qwen3"


def test_provider_uses_configured_openai_client(settings: Settings) -> None:
    with patch("kubesage.ai.factory.Client", autospec=True) as client_class:
        provider = create_ai_provider(settings)

    client_class.assert_called_once_with(
        base_url="http://ollama:11434/v1", api_key="ollama"
    )

    assert isinstance(provider, OpenAICompatibleProvider)


def test_create_ai_provider_rejects_unsupported_provider(settings: Settings) -> None:
    settings.ai_provider = MagicMock()

    with pytest.raises(Exception, match="Unsupported AI provider"):
        create_ai_provider(settings)
