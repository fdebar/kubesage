from unittest.mock import Mock

from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_report import AIReport
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.services.ai_report_generator import AIReportGenerator
from kubesage.services.ai_service import AIService


def test_generate_builds_context_prompt_and_report() -> None:
    ai = Mock(spec=AIService)
    context_builder = Mock(spec=AIContextBuilder)
    prompt_builder = Mock(spec=PromptBuilder)

    incident = Mock(spec=Incident)
    intelligence = Mock(spec=IncidentIntelligence)
    context = Mock()
    report = AIReport(
        summary="summary",
        root_cause="root cause",
        evidence=[],
    )

    context_builder.build.return_value = context
    prompt_builder.build.return_value = "prompt"
    ai.analyze.return_value = report

    generator = AIReportGenerator(
        ai=ai,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
    )

    result = generator.generate(incident, intelligence)

    assert result == report
    context_builder.build.assert_called_once_with(incident, intelligence)
    prompt_builder.build.assert_called_once_with(context)
    ai.analyze.assert_called_once_with("prompt")
