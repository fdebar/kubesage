import structlog

from kubesage.models.analysis import AnalysisTrigger
from kubesage.observability.metrics import (
    ANALYSIS_TOTAL,
    WATCHER_INCIDENTS_DETECTED_TOTAL,
    WATCHER_INCIDENTS_IGNORED_TOTAL,
)
from kubesage.services.analysis_service import AnalysisService
from kubesage.utils.exceptions import PodNotFoundError
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

        for pod in event_source.initial_pods():
            self.state_cache.update(pod)

        logger.info("watcher_state_cache_initialized")

        for event in event_source.watch():
            trigger = self._evaluate_event(event)

            if trigger is None:
                continue

            WATCHER_INCIDENTS_DETECTED_TOTAL.labels(reason=trigger.reason).inc()

            if not self.deduplicator.should_process(trigger):
                logger.info(
                    "watcher_incident_ignored_duplicate",
                    namespace=trigger.namespace,
                    pod=trigger.pod,
                    pod_uid=trigger.pod_uid,
                    reason=trigger.reason,
                )
                WATCHER_INCIDENTS_IGNORED_TOTAL.labels(reason=trigger.reason).inc()
                continue

            self.handle(trigger)

    def handle(self, trigger: IncidentTrigger) -> None:
        logger.info(
            "watcher_incident_trigger_received",
            namespace=trigger.namespace,
            pod=trigger.pod,
            pod_uid=trigger.pod_uid,
            reason=trigger.reason,
        )

        try:
            self.analysis_service.analyze(
                trigger.namespace,
                trigger.pod,
                AnalysisTrigger.WATCHER,
            )
        except PodNotFoundError:
            ANALYSIS_TOTAL.labels(status="error").inc()
            logger.info(
                "Pod '%s' no longer exists in namespace '%s'. Skipping analysis.",
                trigger.pod,
                trigger.namespace,
            )
        except Exception:
            ANALYSIS_TOTAL.labels(status="error").inc()
            logger.exception(
                "Failed to analyze pod '%s' in namespace '%s'.",
                trigger.pod,
                trigger.namespace,
            )

    def _evaluate_event(self, event: PodWatchEvent) -> IncidentTrigger | None:
        if event.type != "MODIFIED":
            return None

        pod = event.pod
        if pod.metadata is None:
            return None

        namespace = pod.metadata.namespace
        name = pod.metadata.name
        uid = pod.metadata.uid
        if namespace is None or name is None or uid is None:
            return None

        previous = self.state_cache.get(namespace, name)
        diff = self.diff_builder.build(previous, pod)

        logger.debug(
            "watcher_state_diff",
            namespace=namespace,
            pod=name,
            previous_found=previous is not None,
            previous_waiting_reason=diff.previous_waiting_reason,
            current_waiting_reason=diff.current_waiting_reason,
            waiting_reason_changed=diff.waiting_reason_changed,
            previous_restart_count=diff.previous_restart_count,
            current_restart_count=diff.current_restart_count,
            restart_delta=diff.restart_delta,
        )

        self.state_cache.update(pod)

        return self.event_filter.evaluate(diff, namespace, name, uid)
