from unittest.mock import MagicMock

import pytest
from openai import APIConnectionError, APIStatusError

from kubesage.ai.providers.openai_compatible import OpenAICompatibleProvider
from kubesage.models.ai_report import AIReport


@pytest.fixture
def client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def provider(client: MagicMock) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(client=client, model="qwen3")


def test_analyze_returns_ai_report(
    provider: OpenAICompatibleProvider, client: MagicMock
) -> None:
    expected_report = AIReport(summary="Pod is crashing due to memory pressure.")

    response = MagicMock()
    response.choices[0].message.parsed = expected_report
    response.usage.total_tokens = 100

    client.chat.completions.parse.return_value = response
    result = provider.analyze("Analyze this CrashLoopBackOff incident.")

    assert result == expected_report

    client.chat.completions.parse.assert_called_once()


def test_analyze_returns_fallback_report_on_error(
    provider: OpenAICompatibleProvider,
    client: MagicMock,
) -> None:
    client.chat.completions.parse.side_effect = Exception("Ollama unavailable")

    result = provider.analyze("Analyze this incident.")

    assert result.summary == ("AI analysis could not be completed.")


def test_analyze_returns_fallback_report_when_response_empty(
    provider: OpenAICompatibleProvider,
    client: MagicMock,
) -> None:
    response = MagicMock()
    response.choices[0].message.parsed = None

    client.chat.completions.parse.return_value = response

    result = provider.analyze("Analyze this incident.")

    assert result.summary == ("AI analysis could not be completed.")


def test_server_is_reachable(
    provider: OpenAICompatibleProvider,
    client: MagicMock,
) -> None:
    client.models.list.return_value = MagicMock()

    assert provider.is_server_reachable() is True

    client.models.list.assert_called_once()


def test_server_is_not_reachable_on_connection_error(
    provider: OpenAICompatibleProvider,
    client: MagicMock,
) -> None:
    client.models.list.side_effect = APIConnectionError(request=MagicMock())

    assert provider.is_server_reachable() is False


def test_server_is_reachable_when_server_returns_http_error(
    provider: OpenAICompatibleProvider,
    client: MagicMock,
) -> None:
    client.models.list.side_effect = APIStatusError(
        message="Unauthorized",
        response=MagicMock(),
        body=None,
    )

    assert provider.is_server_reachable() is True
