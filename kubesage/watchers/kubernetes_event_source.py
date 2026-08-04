from collections.abc import Iterator

import structlog
from kubernetes import watch

from kubesage.utils.kube_client import create_core_v1_api
from kubesage.watchers.models import PodWatchEvent

logger = structlog.get_logger()


class KubernetesPodEventSource:
    """
    Kubernetes implementation of an EventSource.
    Watches pod changes and exposes internal PodWatchEvent objects.
    """

    def __init__(self) -> None:
        self.api = create_core_v1_api()
        if self.api is None:
            raise RuntimeError("Unable to initialize Kubernetes client.")

        self.watcher = watch.Watch()

    def watch(self) -> Iterator[PodWatchEvent]:
        if self.api is None:
            raise RuntimeError("Unable to initialize Kubernetes client.")

        logger.info("kubernetes_pod_watcher_started")
        while True:
            try:
                for event in self.watcher.stream(
                    self.api.list_pod_for_all_namespaces,
                    timeout_seconds=300,
                ):
                    pod = event.get("object")
                    if pod is None:
                        continue

                    yield PodWatchEvent(type=event["type"], pod=pod)

            except Exception:
                logger.warning("kubernetes_pod_watcher_restarting")
