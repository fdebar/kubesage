import structlog

from kubesage.models.ai_context import AIContext
from kubesage.models.incident import Incident
from kubesage.models.incident_intelligence import IncidentIntelligence

logger = structlog.get_logger()


class AIContextBuilder:
    def build(
        self,
        incident: Incident,
        intelligence: IncidentIntelligence,
    ) -> AIContext:
        logger.info(
            "ai_context_building_started",
            namespace=incident.namespace,
            pod=incident.pod,
        )

        context = AIContext(incident, intelligence)

        logger.info(
            "ai_context_building_completed",
            namespace=incident.namespace,
            pod=incident.pod,
            timeline_events_count=len(intelligence.timeline),
        )

        return context
