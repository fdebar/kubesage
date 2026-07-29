import structlog

from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.services.finding_ranker import FindingRanker

logger = structlog.get_logger()


class AIContextBuilder:
    def build(self, incident: Incident, findings: list[Finding]) -> AIContext:
        logger.info(
            "ai_context_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        context = AIContext(incident=incident, findings=FindingRanker().rank(findings))

        logger.info(
            "ai_context_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
            context=context.ctx.model_dump(),
        )

        return context
