import structlog

from kubesage.builders.timeline import TimelineBuilder
from kubesage.models.ai_context import AIContext
from kubesage.models.finding import Finding
from kubesage.models.incident import Incident
from kubesage.services.finding_ranker import FindingRanker

logger = structlog.get_logger()


class AIContextBuilder:
    def __init__(self, timeline_builder: TimelineBuilder | None = None) -> None:
        self.timeline_builder = timeline_builder or TimelineBuilder()

    def build(self, incident: Incident, findings: list[Finding]) -> AIContext:
        logger.info(
            "ai_context_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        timeline = self.timeline_builder.build(incident)

        context = AIContext(
            incident=incident,
            findings=FindingRanker().rank(findings),
            timeline=timeline,
        )

        logger.info(
            "ai_context_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
            timeline_events_count=len(timeline),
        )

        return context
