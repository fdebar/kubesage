from unittest.mock import MagicMock, patch

from kubernetes.watch.watch import SimpleNamespace

from kubesage.models.ai_report import AIReport
from kubesage.services.ai_service import AIService


@patch("kubesage.services.ai_service.OPENAI_DURATION")
@patch("kubesage.services.ai_service.OPENAI_REQUESTS")
@patch("kubesage.services.ai_service.OPENAI_TOKENS")
@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_success(
    mock_openai_class: MagicMock,
    mock_tokens: MagicMock,
    mock_requests: MagicMock,
    mock_duration: MagicMock,
) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    expected_report = AIReport(
        summary="Test summary",
        root_cause="Test",
        evidence=["Test"],
        recommendations=["Test"],
        additional_investigations=["Test"],
    )

    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                parsed=expected_report,
            )
        )
    ]

    mock_response.usage = SimpleNamespace(total_tokens=100)
    mock_client.chat.completions.parse.return_value = mock_response

    service = AIService()
    ai_report = service.analyze("Test prompt")

    assert ai_report == expected_report

    mock_client.chat.completions.parse.assert_called_once()

    mock_duration.observe.assert_called_once()
    mock_requests.labels.assert_called_once_with(status="success")
    mock_requests.labels.return_value.inc.assert_called_once()
    mock_tokens.observe.assert_called_once_with(100)


@patch("kubesage.services.ai_service.OpenAI")
def test_analyze_failure(mock_openai_class: MagicMock) -> None:
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client

    mock_client.chat.completions.parse.side_effect = Exception("OpenAI API Down")

    service = AIService()
    ai_report = service.analyze("Test prompt")

    assert ai_report == AIReport(
        summary="AI analysis could not be completed.",
        root_cause="",
        evidence=[],
        recommendations=[],
        additional_investigations=[],
    )

    @patch("kubesage.services.ai_service.OpenAI")
    def test_analyze_no_parsed_response(mock_openai_class: MagicMock) -> None:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(parsed=None))]

        mock_client.chat.completions.parse.assert_called_once()

        service = AIService()
        report = service.analyze("Test prompt")

        assert report.summary == "AI analysis could not be completed."
