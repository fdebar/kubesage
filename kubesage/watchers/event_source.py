from collections.abc import Iterator
from typing import Protocol

from kubesage.watchers.models import PodWatchEvent


class EventSource(Protocol):
    """
    Contract for objects able to produce watch events.
    """

    def watch(self) -> Iterator[PodWatchEvent]: ...
