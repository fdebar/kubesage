from unittest.mock import MagicMock, patch

from kubesage.services.ai_service import AIService


@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_success(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(content='{"summary": "Test summary", "severity": "High"}')
        )
    ]
    mock_client.chat.completions.create.return_value = mock_response
    service = AIService()

    result = service.analyze("Test prompt")

    assert result == {"summary": "Test summary", "severity": "High"}
    mock_client.chat.completions.create.assert_called_once()


@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_failure(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("OpenAI API Down")
    service = AIService()

    result = service.analyze("Test prompt")

    assert result == {
        "summary": "AI analysis could not be completed.",
        "severity": "Unknown",
        "root_cause": "",
        "recommendations": [],
        "kubectl_commands": [],
    }
    mock_client.chat.completions.create.assert_called_once()
