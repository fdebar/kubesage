import time
from collections.abc import Iterator
from typing import Any

import structlog
from kubernetes import watch
from kubernetes.client import V1Pod

from kubesage.observability.metrics import (
    WATCHER_ERRORS_TOTAL,
    WATCHER_EVENTS_TOTAL,
)
from kubesage.utils.kube_client import create_core_v1_api
from kubesage.watchers.models.incident_trigger import PodWatchEvent

logger = structlog.get_logger()


class KubernetesPodEventSource:
    """
    Kubernetes implementation of an EventSource.
    Provides initial Pod states and watches subsequent changes.
    """

    def __init__(self) -> None:
        self.api = create_core_v1_api()
        self.watcher = watch.Watch()

    def initial_pods(self) -> Iterator[V1Pod]:
        response = self.api.list_pod_for_all_namespaces()

        yield from response.items

    def watch(self) -> Iterator[PodWatchEvent]:
        logger.info("kubernetes_pod_watcher_started")

        while True:
            try:
                for event in self._stream():
                    WATCHER_EVENTS_TOTAL.labels(event_type=event["type"]).inc()
                    pod = event.get("object")
                    if pod is None:
                        continue

                    yield PodWatchEvent(type=event["type"], pod=pod)
            except Exception:
                logger.warning("kubernetes_pod_watcher_restart_failed")
                WATCHER_ERRORS_TOTAL.inc()
                time.sleep(5)
                logger.info("kubernetes_pod_watcher_retrying")

    def _stream(self) -> Any:
        return self.watcher.stream(
            self.api.list_pod_for_all_namespaces, timeout_seconds=300
        )
