from collections.abc import Iterator

import structlog

from kubesage.utils.kube_client import create_core_v1_api, create_watch
from kubesage.watchers.models import PodWatchEvent

logger = structlog.get_logger()


class KubernetesEventSource:
    """
    Produces IncidentTrigger objects from Kubernetes events.
    """

    def __init__(self) -> None:
        self._api = create_core_v1_api()

        if self._api is None:
            raise RuntimeError("Unable to initialize Kubernetes client.")

        self._watch = create_watch()

    def watch(self) -> Iterator[PodWatchEvent]:
        if self._api is None:
            raise RuntimeError("Unable to initialize Kubernetes client.")

        for event in self._watch.stream(
            self._api.list_pod_for_all_namespaces,
            timeout_seconds=300,
        ):
            pod = event.get("object")

            if pod is None:
                continue

            yield PodWatchEvent(
                type=event["type"],
                pod=pod,
            )
