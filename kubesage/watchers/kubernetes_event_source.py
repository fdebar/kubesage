from collections.abc import Iterator
from typing import Any

import structlog
from kubernetes import watch
from kubernetes.client import V1Pod
from kubernetes.client.exceptions import ApiException

from kubesage.observability.metrics import WATCHER_EVENTS_TOTAL
from kubesage.utils.kube_client import create_core_v1_api
from kubesage.watchers.event_source import EventSource, PodListSnapshot
from kubesage.watchers.models.incident_trigger import PodWatchEvent

logger = structlog.get_logger()


class WatchExpiredError(RuntimeError):
    """
    Raised when Kubernetes reports that the requested resourceVersion
    is no longer available.
    """


class KubernetesPodEventSource(EventSource):
    """
    Kubernetes implementation of EventSource.
    """

    def __init__(self) -> None:
        self.api = create_core_v1_api()
        self.watcher = watch.Watch()

    def initial_state(self) -> PodListSnapshot:
        response = self.api.list_pod_for_all_namespaces()

        if response.metadata is None:
            raise RuntimeError("Kubernetes Pod list has no metadata")

        resource_version = response.metadata.resource_version
        if not resource_version:
            raise RuntimeError("Kubernetes Pod list has no resourceVersion")

        return PodListSnapshot(list(response.items), resource_version)

    def watch(self, resource_version: str) -> Iterator[PodWatchEvent]:
        logger.info("kubernetes_pod_watch_started", resource_version=resource_version)

        try:
            for event in self._stream(resource_version):
                event_type = event.get("type")
                obj = event.get("object")

                if event_type == "ERROR":
                    code = self._extract_status_code(obj)

                    if code == 410:
                        raise WatchExpiredError(
                            "Kubernetes watch resourceVersion expired"
                        )

                    logger.error("kubernetes_watch_error_event", code=code, object=obj)
                    continue

                if event_type not in {"ADDED", "MODIFIED", "DELETED"}:
                    continue

                if not isinstance(obj, V1Pod):
                    logger.warning(
                        "kubernetes_watch_invalid_object",
                        event_type=event_type,
                        object_type=type(obj).__name__,
                    )
                    continue

                object_resource_version = None

                if obj.metadata is not None:
                    object_resource_version = obj.metadata.resource_version

                WATCHER_EVENTS_TOTAL.labels(event_type=event_type).inc()

                yield PodWatchEvent(
                    type=event_type,
                    pod=obj,
                    resource_version=object_resource_version,
                )

        except ApiException as exc:
            if exc.status == 410:
                raise WatchExpiredError(
                    "Kubernetes watch resourceVersion expired"
                ) from exc

            raise

    def _stream(self, resource_version: str) -> Any:
        return self.watcher.stream(
            self.api.list_pod_for_all_namespaces,
            resource_version=resource_version,
            timeout_seconds=300,
        )

    @staticmethod
    def _extract_status_code(obj: Any) -> int | None:
        if isinstance(obj, dict):
            code = obj.get("code")

            if code is None:
                return None

            try:
                return int(code)
            except TypeError, ValueError:
                return None

        code = getattr(obj, "code", None)
        if code is None:
            return None

        try:
            return int(code)
        except TypeError, ValueError:
            return None
