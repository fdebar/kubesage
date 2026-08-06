import structlog

from kubesage.models.analysis import Analysis
from kubesage.observability.metrics import (
    WATCHER_INCIDENTS_IGNORED_TOTAL,
)
from kubesage.services.analysis_service import AnalysisService
from kubesage.watchers.event_source import EventSource
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.models.incident_trigger import IncidentTrigger, PodWatchEvent
from kubesage.watchers.pod_event_filter import PodEventFilter
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import (
    PodStateDiffBuilder,
)

logger = structlog.get_logger()


class KubernetesWatcher:
    def __init__(
        self,
        analysis_service: AnalysisService,
        event_filter: PodEventFilter,
        deduplicator: IncidentDeduplicator,
        state_cache: PodStateCache,
        diff_builder: PodStateDiffBuilder,
    ):
        self.analysis_service = analysis_service
        self.event_filter = event_filter
        self.deduplicator = deduplicator
        self.state_cache = state_cache
        self.diff_builder = diff_builder

    def start(self, event_source: EventSource) -> None:
        logger.info("watcher_started")

        for event in event_source.watch():
            trigger = self._evaluate_event(event)
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

    def _evaluate_event(self, event: PodWatchEvent) -> IncidentTrigger | None:
        pod = event.pod
        if pod.metadata is None:
            return None

        namespace = pod.metadata.namespace
        name = pod.metadata.name
        if namespace is None or name is None:
            return None

        previous = self.state_cache.get(namespace, name)
        diff = self.diff_builder.build(previous, pod)
        self.state_cache.update(pod)

        trigger = self.event_filter.evaluate(diff, namespace, name)
        if trigger:
            return trigger

        return self.event_filter.build_trigger(event)
