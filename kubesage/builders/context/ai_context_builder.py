import structlog

from kubesage.builders.context.metrics_builder import MetricsBuilder
from kubesage.builders.context.summary_builder import SummaryBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident

logger = structlog.get_logger()


class AIContextBuilder:
    def __init__(self) -> None:
        self.summary_builder = SummaryBuilder()
        self.metrics_builder = MetricsBuilder()

    def build(self, incident: Incident, findings: list[Finding]) -> AIContext:
        logger.info(
            "ai_context_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        context = AIContext(
            incident=incident,
            findings=findings,
            summary=self.summary_builder.build(findings),
            metrics_summary=self.metrics_builder.build(incident),
        )

        logger.info(
            "ai_context_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        return context
