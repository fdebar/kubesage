from unittest.mock import MagicMock, patch

from kubesage.models.incident import Incident
from kubesage.services.incident_service import IncidentService


@patch("kubesage.services.incident_service.DiagnosticEngine")
@patch("kubesage.services.incident_service.ContextBuilder")
@patch("kubesage.services.incident_service.PromptBuilder")
@patch("kubesage.services.incident_service.AIService")
@patch("kubesage.services.incident_service.IncidentBuilder")
def test_analyze_flow(
    incident_builder_cls: MagicMock,
    ai_cls: MagicMock,
    prompt_builder_cls: MagicMock,
    context_builder_cls: MagicMock,
    engine_cls: MagicMock,
) -> None:
    # IncidentBuilder
    incident = MagicMock(spec=Incident)

    incident_builder = MagicMock()
    incident_builder.collect.return_value = incident
    incident_builder_cls.return_value = incident_builder

    # DiagnosticEngine
    findings = ["finding1", "finding2"]

    engine = MagicMock()
    engine.analyze.return_value = findings
    engine_cls.return_value = engine

    # ContextBuilder
    context = MagicMock()

    context_builder = MagicMock()
    context_builder.build.return_value = context
    context_builder_cls.return_value = context_builder

    # PromptBuilder
    prompt = "Constructed prompt"

    prompt_builder = MagicMock()
    prompt_builder.build.return_value = prompt
    prompt_builder_cls.return_value = prompt_builder

    # AIService
    report = {"summary": "AI diagnosis report"}

    ai = MagicMock()
    ai.analyze.return_value = report
    ai_cls.return_value = ai

    # Execute
    service = IncidentService()

    result = service.analyze("default", "my-pod")

    # Assert
    assert result == report

    incident_builder.collect.assert_called_once_with(
        "default",
        "my-pod",
    )

    engine.analyze.assert_called_once_with(incident)

    context_builder.build.assert_called_once_with(
        incident,
        findings,
    )

    prompt_builder.build.assert_called_once_with(context)

    ai.analyze.assert_called_once_with(prompt)
