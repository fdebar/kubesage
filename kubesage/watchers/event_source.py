from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from kubernetes.client import V1Pod

from kubesage.watchers.models.incident_trigger import PodWatchEvent


@dataclass(frozen=True)
class PodListSnapshot:
    pods: list[V1Pod]
    resource_version: str


class EventSource(Protocol):
    """
    Contract for objects able to produce Kubernetes Pod snapshots and watch
    subsequent changes.
    """

    def initial_state(self) -> PodListSnapshot:
        """Return the current Pods and the collection resourceVersion."""

        raise NotImplementedError

    def watch(self, resource_version: str) -> Iterator[PodWatchEvent]:
        """Watch Pod changes starting exactly after resource_version."""

        raise NotImplementedError
