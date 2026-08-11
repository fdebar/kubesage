from collections.abc import Iterator
from typing import Protocol

from kubernetes.client import V1Pod

from kubesage.watchers.models.incident_trigger import PodWatchEvent


class EventSource(Protocol):
    """
    Contract for objects able to produce watch events.
    """

    def initial_pods(self) -> Iterator[V1Pod]:
        """Yields all pods at the time the watcher is started.
        This is used to populate the initial state cache.
        """

        raise NotImplementedError

    def watch(self) -> Iterator[PodWatchEvent]:
        """Yields watch events as they arrive.
        This should include all pod events that may be interesting to the watcher.
        """

        raise NotImplementedError
