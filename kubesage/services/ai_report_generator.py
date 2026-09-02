from kubesage.builders.context.ai_context_builder import AIContextBuilder
from kubesage.builders.prompt.prompt_builder import PromptBuilder
from kubesage.models.ai_report import AIReport
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence
from kubesage.services.ai_service import AIService


class AIReportGenerator:
    """Build the AI context and prompt, then generate an incident report."""

    def __init__(
        self,
        ai: AIService,
        context_builder: AIContextBuilder,
        prompt_builder: PromptBuilder,
    ) -> None:
        self.ai = ai
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder

    def generate(
        self,
        incident: Incident,
        intelligence: IncidentIntelligence,
    ) -> AIReport:
        context = self.context_builder.build(incident, intelligence)
        prompt = self.prompt_builder.build(context)
        return self.ai.analyze(prompt)
