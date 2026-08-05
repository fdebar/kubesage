import structlog

from kubesage.models.analysis import Analysis
from kubesage.observability.metrics import (
    WATCHER_INCIDENTS_IGNORED_TOTAL,
)
from kubesage.services.analysis_service import AnalysisService
from kubesage.watchers.event_source import EventSource
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.models import IncidentTrigger
from kubesage.watchers.pod_event_filter import PodEventFilter

logger = structlog.get_logger()


class KubernetesWatcher:
    def __init__(
        self,
        analysis_service: AnalysisService,
        event_filter: PodEventFilter,
        deduplicator: IncidentDeduplicator,
    ):
        self.analysis_service = analysis_service
        self.event_filter = event_filter
        self.deduplicator = deduplicator

    def start(self, event_source: EventSource) -> None:
        logger.info("watcher_started")

        for event in event_source.watch():
            trigger = self.event_filter.build_trigger(event)
            if trigger is None:
                continue

            if not self.deduplicator.should_process(trigger):
                logger.info(
                    "watcher_incident_ignored_duplicate",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    reason=trigger.reason,
                )
                WATCHER_INCIDENTS_IGNORED_TOTAL.labels(reason=trigger.reason).inc()
                continue

            self.handle(trigger)

    def handle(self, trigger: IncidentTrigger) -> Analysis:
        logger.info(
            "watcher_incident_trigger_received",
            namespace=trigger.namespace,
            pod=trigger.pod,
            reason=trigger.reason,
        )

        return self.analysis_service.analyze(
            namespace=trigger.namespace,
            pod=trigger.pod,
        )
