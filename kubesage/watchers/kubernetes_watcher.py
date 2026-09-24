import time
from collections.abc import Callable

import structlog

from kubesage.observability.metrics import (
    WATCHER_ERRORS_TOTAL,
    WATCHER_INCIDENTS_DETECTED_TOTAL,
    WATCHER_INCIDENTS_IGNORED_TOTAL,
    WATCHER_RECONNECTS_TOTAL,
    WATCHER_RESYNCS_TOTAL,
)
from kubesage.watchers.event_source import EventSource
from kubesage.watchers.incident_deduplicator import IncidentDeduplicator
from kubesage.watchers.kubernetes_event_source import WatchExpiredError
from kubesage.watchers.models.incident_trigger import (
    IncidentTrigger,
    PodWatchEvent,
)
from kubesage.watchers.pod_event_filter import PodEventFilter
from kubesage.watchers.pod_state_cache import PodStateCache
from kubesage.watchers.pod_state_diff_builder import PodStateDiffBuilder

logger = structlog.get_logger()

AnalysisSubmitter = Callable[[IncidentTrigger], None]


class KubernetesWatcher:
    def __init__(
        self,
        event_filter: PodEventFilter,
        deduplicator: IncidentDeduplicator,
        state_cache: PodStateCache,
        diff_builder: PodStateDiffBuilder,
        analysis_submitter: AnalysisSubmitter,
        max_backoff_seconds: int = 60,
    ) -> None:
        self.event_filter = event_filter
        self.deduplicator = deduplicator
        self.state_cache = state_cache
        self.diff_builder = diff_builder
        self.analysis_submitter = analysis_submitter
        self.max_backoff_seconds = max_backoff_seconds

    def start(
        self,
        event_source: EventSource,
        stop_when_watch_ends: bool = False,
    ) -> None:
        logger.info("watcher_started")

        resource_version: str | None = None
        backoff_seconds = 1

        while True:
            try:
                if resource_version is None:
                    snapshot = event_source.initial_state()
                    self.state_cache.replace(snapshot.pods)
                    resource_version = snapshot.resource_version

                    logger.info(
                        "watcher_state_cache_initialized",
                        pods=len(snapshot.pods),
                        resource_version=resource_version,
                    )

                for event in event_source.watch(resource_version):
                    if event.resource_version:
                        resource_version = event.resource_version

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
                            resource_version=trigger.resource_version,
                            reason=trigger.reason,
                        )

                        WATCHER_INCIDENTS_IGNORED_TOTAL.labels(
                            reason=trigger.reason
                        ).inc()

                        continue

                    logger.info(
                        "watcher_incident_queued",
                        namespace=trigger.namespace,
                        pod=trigger.pod,
                        pod_uid=trigger.pod_uid,
                        resource_version=trigger.resource_version,
                        reason=trigger.reason,
                    )

                    try:
                        self.analysis_submitter(trigger)
                    except Exception:
                        self.deduplicator.forget(trigger)
                        raise
                if stop_when_watch_ends:
                    return

                WATCHER_RECONNECTS_TOTAL.inc()
                backoff_seconds = 1

            except WatchExpiredError:
                logger.warning("watcher_resource_version_expired_resync")

                WATCHER_RESYNCS_TOTAL.inc()

                # Force a new LIST on the next iteration.
                resource_version = None
                backoff_seconds = 1

            except Exception:
                WATCHER_ERRORS_TOTAL.inc()

                logger.exception(
                    "watcher_stream_failed",
                    resource_version=resource_version,
                    retry_in_seconds=backoff_seconds,
                )

                time.sleep(backoff_seconds)

                backoff_seconds = min(backoff_seconds * 2, self.max_backoff_seconds)

    def _evaluate_event(self, event: PodWatchEvent) -> IncidentTrigger | None:
        pod = event.pod

        metadata = pod.metadata
        if metadata is None:
            return None

        namespace = metadata.namespace
        name = metadata.name
        uid = metadata.uid
        resource_version = event.resource_version or metadata.resource_version

        if namespace is None or name is None or uid is None or resource_version is None:
            return None

        if event.type == "ADDED":
            self.state_cache.update(pod)
            return None

        if event.type == "DELETED":
            self.state_cache.remove(namespace, uid)
            return None

        if event.type != "MODIFIED":
            return None

        previous = self.state_cache.get(namespace, uid)
        diff = self.diff_builder.build(previous, pod)
        self.state_cache.update(pod)

        logger.debug(
            "watcher_state_diff",
            namespace=namespace,
            pod=name,
            pod_uid=uid,
            resource_version=resource_version,
            previous_found=previous is not None,
            previous_waiting_reason=diff.previous_waiting_reason,
            current_waiting_reason=diff.current_waiting_reason,
            waiting_reason_changed=diff.waiting_reason_changed,
            previous_restart_count=diff.previous_restart_count,
            current_restart_count=diff.current_restart_count,
            restart_delta=diff.restart_delta,
        )

        return self.event_filter.evaluate(diff, namespace, name, uid, resource_version)
