from unittest.mock import MagicMock, patch

from kubesage.models.ai_report import AIReport
from kubesage.services.ai_service import AIService


@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_success(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                content='{"summary": "Test summary", "root_cause": "Test", "evidence": ["Test"], "recommendations": ["Test"], "additional_investigations": ["Test"]}'  # noqa: E501
            )
        )
    ]
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    mock_client.chat.completions.create.return_value = mock_response

    service = AIService()
    ai_report = service.analyze("Test prompt")

    assert ai_report == AIReport(
        summary="Test summary",
        root_cause="Test",
        evidence=["Test"],
        recommendations=["Test"],
        additional_investigations=["Test"],
    )
    mock_client.chat.completions.create.assert_called_once()


@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_failure(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.side_effect = Exception("OpenAI API Down")

    service = AIService()
    ai_report = service.analyze("Test prompt")

    assert ai_report == AIReport(
        summary="AI analysis could not be completed.",
        root_cause="",
        recommendations=[],
    )
    mock_client.chat.completions.create.assert_called_once()
