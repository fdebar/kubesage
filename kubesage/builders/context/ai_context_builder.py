import structlog

from kubesage.builders.context.metrics_builder import MetricsBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.services.finding_ranker import FindingRanker

logger = structlog.get_logger()


class AIContextBuilder:
    def __init__(self) -> None:
        self.metrics_builder = MetricsBuilder()

    def build(self, incident: Incident, findings: list[Finding]) -> AIContext:
        logger.info(
            "ai_context_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        ranked_findings = FindingRanker().rank(findings)
        context = AIContext(
            incident=incident,
            findings=ranked_findings,
            metrics_summary=self.metrics_builder.build(incident),
        )

        logger.info(
            "ai_context_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        return context
